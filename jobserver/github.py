import requests
from environs import Env
from furl import furl
from social_core.backends.github import GithubOAuth2
from social_core.exceptions import AuthFailed


env = Env()


BASE_URL = "https://api.github.com"
TOKEN = env.str("GITHUB_TOKEN")
USER_AGENT = "OpenSAFELY Jobs"


def get_branch_sha(repo, branch):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        "opensafely",
        repo,
        "branches",
        branch,
    ]

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {TOKEN}",
        "User-Agent": "OpenSAFELY Jobs",
    }
    r = requests.get(f.url, headers=headers)
    r.raise_for_status()

    return r.json()["commit"]["sha"]


def get_file(repo, branch):
    f = furl(BASE_URL)
    f.path.segments += [
        "repos",
        "opensafely",
        repo,
        "contents",
        "project.yaml",
    ]
    f.args["ref"] = branch

    headers = {
        "Accept": "application/vnd.github.3.raw",
        "Authorization": f"token {TOKEN}",
        "User-Agent": USER_AGENT,
    }
    r = requests.get(f.url, headers=headers)

    if r.status_code == 404:
        return

    r.raise_for_status()

    return r.text


def get_repos_with_branches():
    """
    Get Repos with their branches from the OpenSafely Researchers Team

    This uses the GraphQL API to avoid making O(N) calls to GitHub's (v3) REST
    API.
    """
    query = """
    query {
      organization(login: "opensafely") {
        team(slug: "researchers") {
          repositories(first: 100) {
            nodes {
              name
              url
              refs(refPrefix: "refs/heads/", first: 100) {
                nodes {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    payload = {"query": query}

    headers = {
        "Authorization": f"bearer {TOKEN}",
        "User-Agent": USER_AGENT,
    }
    r = requests.post("https://api.github.com/graphql", headers=headers, json=payload)
    r.raise_for_status()
    repos = r.json()["data"]["organization"]["team"]["repositories"]["nodes"]

    for repo in repos:
        branches = [b["name"] for b in repo["refs"]["nodes"]]

        yield {
            "name": repo["name"],
            "url": repo["url"],
            "branches": branches,
        }


class GithubOrganizationOAuth2(GithubOAuth2):
    """Github OAuth2 authentication backend for organizations"""

    name = "github-org"
    no_member_string = "User doesn't belong to the organization"

    def user_data(self, access_token, *args, **kwargs):
        """
        Check the User is part of our Org

        This is a near-complete reimplementation of GithubMemberOAuth2's
        .user_data() which gets the correct URL from GithubOrganizationOAuth2's
        .member_url().

        We use our service-level PAT to avoid requesting further scopes from
        the user (specifically admin:org) to make the call to the Org
        membership endpoint.
        """
        user_data = super().user_data(access_token, *args, **kwargs)

        # https://docs.github.com/en/free-pro-team@latest/rest/reference/orgs#check-organization-membership-for-a-user
        f = furl(BASE_URL)
        f.path.segments += [
            "orgs",
            "opensafely",
            "members",
            user_data.get("login"),
        ]

        # Use our "service-level" PAT instead of the User's OAuth token to
        # avoid asking for the extra admin:org scope just for this check
        headers = {"Authorization": f"token {TOKEN}"}

        try:
            self.request(f.url, headers=headers)
        except requests.HTTPError as err:
            # if the user is a member of the organization, response code
            # will be 204, see http://bit.ly/ZS6vFl
            if err.response.status_code != 204:
                raise AuthFailed(self, "User doesn't belong to the organization")

        return user_data
