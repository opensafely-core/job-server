import json
from datetime import datetime, timezone

import requests
from environs import Env
from furl import furl


env = Env()


AUTHORIZATION_ORGS = env.list("AUTHORIZATION_ORGS")
BASE_URL = "https://api.github.com"
GITHUB_TOKEN = env.str("GITHUB_TOKEN")


session = requests.Session()
session.headers = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "User-Agent": "OpenSAFELY Jobs",
}


def _get_query_page(*, query, session, cursor, **kwargs):
    """
    Get a page of the given query

    This uses the GraphQL API to avoid making O(N) calls to GitHub's (v3) REST
    API.  The passed cursor is a GraphQL cursor [1] allowing us to call this
    function in a loop, passing in the responses cursor to advance our view of
    the data.

    [1]: https://graphql.org/learn/pagination/#end-of-list-counts-and-connections
    """
    # use GraphQL variables to avoid string interpolation
    variables = {"cursor": cursor, **kwargs}
    payload = {"query": query, "variables": variables}

    r = session.post("https://api.github.com/graphql", json=payload)
    r.raise_for_status()
    results = r.json()

    # In some cases graphql will return a 200 response when there are errors.
    # https://sachee.medium.com/200-ok-error-handling-in-graphql-7ec869aec9bc
    # Handling things robustly is complex and query specific, so here we simply
    # take the absence of 'data' as an error, rather than the presence of
    # 'errors' key.
    if "data" not in results:
        raise RuntimeError(
            f"graphql query failed\n\nquery:\n{query}\n\nresponse:\n{json.dumps(results, indent=2)}"
        )

    return results["data"]["organization"]["team"]["repositories"]


def _iter_query_results(query, **kwargs):
    """
    Get results from a GraphQL query

    Given a GraphQL query, return all results across one or more pages as a
    single generator.  We currently assume all results live under

        data.organization.team.repositories

    GitHub's GraphQL API provides cursor-based pagination, so this function
    wraps the actual API calls done in _get_query_page and tracks the cursor.
    one.
    """
    cursor = ""
    while True:
        data = _get_query_page(
            query=query,
            session=session,
            cursor=cursor,
            **kwargs,
        )

        yield from data["nodes"]

        if not data["pageInfo"]["hasNextPage"]:
            break

        # update the cursor we pass into the GraphQL query
        cursor = data["pageInfo"]["endCursor"]


def get_branch(org, repo, branch):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        org,
        repo,
        "branches",
        branch,
    ]

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    r = session.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.json()


def get_branch_sha(org, repo, branch):
    branch = get_branch(org, repo, branch)

    if branch is None:
        return

    return branch["commit"]["sha"]


def get_commits(org, repo, limit=10):

    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        org,
        repo,
        "commits",
    ]
    f.args["per_page"] = limit

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    r = session.get(f.url, headers=headers)

    r.raise_for_status()

    return r.json()


def get_file(org, repo, branch):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        org,
        repo,
        "contents",
        "project.yaml",
    ]
    f.args["ref"] = branch

    headers = {
        "Accept": "application/vnd.github.3.raw",
    }
    r = session.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.text


def get_repo(org, repo):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        org,
        repo,
    ]

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    r = session.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.json()


def get_repo_is_private(org, repo):
    repo = get_repo(org, repo)

    if repo is None:
        return None

    return repo["private"]


def get_repos_with_branches(org):
    """
    Get Repos (with branches) from the OpenSAFELY Researchers Team

    This uses the GraphQL API to avoid making O(N) calls to GitHub's (v3) REST
    API.  The passed cursor is a GraphQL cursor [1] allowing us to call this
    function in a loop, passing in the responses cursor to advance our view of
    the data.

    [1]: https://graphql.org/learn/pagination/#end-of-list-counts-and-connections
    """
    query = """
    query reposAndBranches($cursor: String, $org_name: String!) {
      organization(login: $org_name) {
        team(slug: "researchers") {
          repositories(first: 100, after: $cursor) {
            nodes {
              name
              url
              refs(refPrefix: "refs/heads/", first: 100) {
                nodes {
                  name
                }
              }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
          }
        }
      }
    }
    """
    results = list(_iter_query_results(query, org_name=org))
    for repo in results:
        branches = [b["name"] for b in repo["refs"]["nodes"]]

        yield {
            "name": repo["name"],
            "url": repo["url"],
            "branches": branches,
        }


def get_repos_with_dates():
    query = """
    query reposAndBranches($cursor: String) {
      organization(login: "opensafely") {
        team(slug: "researchers") {
          repositories(first: 100, after: $cursor) {
            nodes {
              name
              url
              isPrivate
              createdAt
              repositoryTopics(first: 100) {
                nodes {
                  topic {
                    name
                  }
                }
              }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
          }
        }
      }
    }
    """
    results = list(_iter_query_results(query))
    for repo in results:
        created_at = datetime.strptime(repo["createdAt"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

        topics = []
        if repo["repositoryTopics"]["nodes"]:
            topics = [n["topic"]["name"] for n in repo["repositoryTopics"]["nodes"]]

        yield {
            "name": repo["name"],
            "url": repo["url"],
            "is_private": repo["isPrivate"],
            "created_at": created_at,
            "topics": topics,
        }


def is_member_of_org(org, username):
    # https://docs.github.com/en/rest/reference/orgs#check-organization-membership-for-a-user
    f = furl(BASE_URL)
    f.path.segments += [
        "orgs",
        org,
        "members",
        username,
    ]

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    r = session.get(f.url, headers=headers)

    if r.status_code == 204:
        return True

    if r.status_code in (302, 404):
        return False

    r.raise_for_status()
