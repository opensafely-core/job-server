import requests
from environs import Env
from furl import furl


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
