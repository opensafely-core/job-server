import json

import requests
from environs import Env
from furl import furl


env = Env()


BASE_URL = "https://api.github.com"
GITHUB_TOKEN = env.str("GITHUB_TOKEN")
USER_AGENT = "OpenSAFELY Jobs"


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
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": USER_AGENT,
    }
    r = requests.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.json()


def get_branch_sha(org, repo, branch):
    branch = get_branch(org, repo, branch)

    if branch is None:
        return

    return branch["commit"]["sha"]


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
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": USER_AGENT,
    }
    r = requests.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.text


def _get_page(session, org, cursor):
    """
    Get a page of Repos (with branches) from the OpenSAFELY Researchers Team

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
    # use GraphQL variables to avoid string interpolation
    variables = {"cursor": cursor, "org_name": org}
    payload = {"query": query, "variables": variables}

    r = session.post("https://api.github.com/graphql", json=payload)
    r.raise_for_status()
    result = r.json()

    # In some cases graphql will return a 200 response when there are errors.
    # https://sachee.medium.com/200-ok-error-handling-in-graphql-7ec869aec9bc
    # Handling things robustly is complex and query specific, so here we simply
    # take the absence of 'data' as an error, rather than the presence of
    # 'errors' key.
    if "data" not in result:
        raise RuntimeError(
            f"graphql query failed\n\nquery:\n{query}\n\nresponse:\n{json.dumps(result, indent=2)}"
        )

    return r.json()["data"]["organization"]["team"]["repositories"]


def get_repos_with_branches(org):
    """
    Get Repos (with branches) from the OpenSAFELY Researchers Team

    GitHub limits their paged endpoints to 100 items so we need to paginate the
    repositories section of our GraphQL query.  GraphQL uses cursors for
    pagination (more info in the _get_page function).  We start with an empty
    cursor to get the first page then update it from the response of each page.
    """
    session = requests.Session()
    session.headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "User-Agent": USER_AGENT,
    }

    cursor = ""
    while True:
        data = _get_page(session, org, cursor)

        # build a dictionary for each repo with it's branches
        for repo in data["nodes"]:
            branches = [b["name"] for b in repo["refs"]["nodes"]]

            yield {
                "name": repo["name"],
                "url": repo["url"],
                "branches": branches,
            }

        if not data["pageInfo"]["hasNextPage"]:
            break

        # update the cursor we pass into the GraphQL query
        cursor = data["pageInfo"]["endCursor"]


def is_member_of_org(org, username):
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/orgs#check-organization-membership-for-a-user
    f = furl(BASE_URL)
    f.path.segments += [
        "orgs",
        org,
        "members",
        username,
    ]

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": USER_AGENT,
    }

    r = requests.get(f.url, headers=headers)

    return r.status_code == 204
