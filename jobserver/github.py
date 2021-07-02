import json

import requests
from environs import Env
from furl import furl
from social_core.backends.github import GithubOAuth2
from social_core.exceptions import AuthFailed


env = Env()


AUTHORIZATION_ORGS = env.list("AUTHORIZATION_ORGS")
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


def get_repo(org, repo):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        org,
        repo,
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


def get_repo_is_private(org, repo):
    repo = get_repo(org, repo)

    if repo is None:
        return None

    return repo["private"]


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
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": USER_AGENT,
    }

    r = requests.get(f.url, headers=headers)

    return r.status_code == 204


class GithubOrganizationOAuth2(GithubOAuth2):
    """Github OAuth2 authentication backend for organizations"""

    no_member_string = "User doesn't belong to the organization"

    # Mirror our initial Social Auth Backend choice (GithubOAuth2) provider's
    # name because it's simpler than making a migration which modifies the
    # UserSocialAuth table.  Our jobserver app defines a Custom User Model
    # which social_django depends on in it's migrations dependency tree
    # (because it FKs User).  This appears to make migrations hit a catch-22 in
    # dependency resolution.  Rather than dig through the resolver, this is a
    # much easier fix.
    name = "github"

    def user_data(self, access_token, *args, **kwargs):
        """
        Check the User is part of a configured GitHub Org

        This is a near-complete reimplementation of GithubMemberOAuth2's
        .user_data() which gets the correct URL from GithubOrganizationOAuth2's
        .member_url().

        We use our service-level PAT to avoid requesting further scopes from
        the user (specifically admin:org) to make the call to the Org
        membership endpoint.
        """
        user_data = super().user_data(access_token, *args, **kwargs)
        username = user_data.get("login")

        for org in AUTHORIZATION_ORGS:
            if is_member_of_org(org, username):
                return user_data  # succeed on the first valid org

        msg = (
            f'"{username}" is not part of the OpenSAFELY GitHub Organization. '
            '<a href="https://opensafely.org/contact/">Contact us</a> to request access.'
        )
        raise AuthFailed(self, msg)
