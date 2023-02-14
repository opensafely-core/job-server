import json
from datetime import datetime, timezone

import requests
from environs import Env
from furl import furl


env = Env()


GITHUB_TOKEN = env.str("GITHUB_TOKEN")


session = requests.Session()
session.headers = {
    "User-Agent": "OpenSAFELY Jobs",
}


class GitHubError(Exception):
    """Base exception to target all other exceptions we define here"""

    pass


class RepoAlreadyExists(GitHubError):
    pass


class GitHubAPI:
    """
    A thin wrapper around requests, furl, and the GitHub API.

    Initialising this class with a token will set that token in the sessions
    headers.

    "public" functions should construct a URL and make requests against the
    session object attached to the instance.

    This object is not expected to be used in most tests so we can avoid mocking.
    """

    base_url = "https://api.github.com"

    def __init__(self, _session=session, token=None):
        """
        Initialise the wrapper with a session and maybe token

        We pass in the session here so that tests can pass in a fake object to
        test internals.
        """
        self.session = _session
        self.token = token

    def _delete(self, *args, **kwargs):
        return self._request("delete", *args, **kwargs)

    def _get(self, *args, **kwargs):
        return self._request("get", *args, **kwargs)

    def _post(self, *args, **kwargs):
        return self._request("post", *args, **kwargs)

    def _put(self, *args, **kwargs):
        return self._request("put", *args, **kwargs)

    def _request(self, method, *args, **kwargs):
        """
        Thin wrapper of requests.Session._request()

        This wrapper exists solely to inject the Authorization header if a
        token has been set on the current instance and that headers hasn't
        already been set in a given requests headers.

        This solves a tension between using an application-level session object
        and wanting GitHubAPI instance-level authentication.  We want to
        support the use of different tokens for typical running (eg in prod),
        verification tests (eg in CI), and the ability to query the API without
        a token (less likely but can be useful) so we can't just set the header
        on the session when it's defined at the module level.  However if we
        set it on the session then it persists beyond the life time of a given
        GitHubAPI instance.
        """
        headers = kwargs.pop("headers", {})

        if self.token and "Authorization" not in headers:
            headers = headers | {"Authorization": f"bearer {self.token}"}

        return self.session.request(method, *args, headers=headers, **kwargs)

    def _get_query_page(self, *, query, session, cursor, **kwargs):
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

        r = self._post("https://api.github.com/graphql", json=payload)
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

        return results["data"]["organization"]["repositories"]

    def _iter_query_results(self, query, **kwargs):
        """
        Get results from a GraphQL query

        Given a GraphQL query, return all results across one or more pages as a
        single generator.  We currently assume all results live under

            data.organization.team.repositories

        GitHub's GraphQL API provides cursor-based pagination, so this function
        wraps the actual API calls done in _get_query_page and tracks the cursor.
        one.
        """
        cursor = None
        while True:
            data = self._get_query_page(
                query=query,
                session=session,
                cursor=cursor,
                **kwargs,
            )

            yield from data["nodes"]

            if not data["pageInfo"]["hasNextPage"]:
                break

            # update the cursor we pass into the GraphQL query
            cursor = data["pageInfo"]["endCursor"]  # pragma: no cover

    def _url(self, path_segments, query_args=None):
        f = furl(self.base_url)

        f.path.segments = path_segments

        if query_args:
            f.add(query_args)

        return f.url

    def add_repo_to_team(self, team, org, repo):
        path_segments = [
            "orgs",
            org,
            "teams",
            team,
            "repos",
            org,
            repo,
        ]
        url = self._url(path_segments)

        payload = {
            "permission": "maintain",
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._put(url, headers=headers, json=payload)

        r.raise_for_status()

        return

    def create_issue(self, org, repo, title, body, labels):
        path_segments = [
            "repos",
            org,
            repo,
            "issues",
        ]
        url = self._url(path_segments)

        payload = {
            "title": title,
            "body": body,
            "labels": labels,
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._post(url, headers=headers, json=payload)

        r.raise_for_status()

        return r.json()

    def create_repo(self, org, repo):
        path_segments = [
            "orgs",
            org,
            "repos",
        ]
        url = self._url(path_segments)

        payload = {
            "name": repo,
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._post(url, headers=headers, json=payload)

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RepoAlreadyExists from e

        return r.json()

    def delete_repo(self, org, repo):  # pragma: no cover
        """
        Delete the given repo

        This exists to help with testing create_repo().  Since it only runs
        against the live GitHub API and we don't control state there we're
        ignoring coverage for the whole method.
        """
        path_segments = [
            "repos",
            org,
            repo,
        ]
        url = self._url(path_segments)

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._delete(url, headers=headers)

        if r.status_code == 404:
            return

        r.raise_for_status()

    def get_branch(self, org, repo, branch):
        path_segments = [
            "repos",
            org,
            repo,
            "branches",
            branch,
        ]
        url = self._url(path_segments)

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._get(url, headers=headers)

        if r.status_code == 404:
            return

        r.raise_for_status()

        return r.json()

    def get_branches(self, org, repo):
        path_segments = [
            "repos",
            org,
            repo,
            "branches",
        ]
        url = self._url(path_segments)

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._get(url, headers=headers)

        if r.status_code == 404:
            return []

        r.raise_for_status()

        return r.json()

    def get_branch_sha(self, org, repo, branch):
        branch = self.get_branch(org, repo, branch)

        if branch is None:
            return

        return branch["commit"]["sha"]

    def get_file(self, org, repo, branch):
        path_segments = [
            "repos",
            org,
            repo,
            "contents",
            "project.yaml",
        ]
        query_args = {"ref": branch}
        url = self._url(path_segments, query_args)

        headers = {
            "Accept": "application/vnd.github.3.raw",
        }
        r = self._get(url, headers=headers)

        if r.status_code == 404:
            return

        r.raise_for_status()

        return r.text

    def get_repo(self, org, repo):
        path_segments = [
            "repos",
            org,
            repo,
        ]
        url = self._url(path_segments)

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._get(url, headers=headers)

        if r.status_code == 404:
            return

        r.raise_for_status()

        return r.json()

    def get_repo_is_private(self, org, repo):
        repo = self.get_repo(org, repo)

        if repo is None:
            return None

        return repo["private"]

    def get_repos_with_branches(self, org):
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
            repositories(first: 100, after: $cursor) {
              nodes {
                name
                url
                refs(refPrefix: "refs/heads/", first: 100) {
                  nodes {
                    name
                  }
                }
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
        """
        results = list(self._iter_query_results(query, org_name=org))
        for repo in results:
            branches = [b["name"] for b in repo["refs"]["nodes"]]

            topics = []
            if repo["repositoryTopics"]["nodes"]:
                topics = [n["topic"]["name"] for n in repo["repositoryTopics"]["nodes"]]

            if "non-research" in topics:
                continue  # ignore non-research repos

            yield {
                "name": repo["name"],
                "url": repo["url"],
                "branches": branches,
            }

    def get_repos_with_dates(self, org):
        query = """
        query reposAndBranches($cursor: String, $org_name: String!) {
          organization(login: $org_name) {
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
        """
        results = list(self._iter_query_results(query, org_name=org))
        for repo in results:
            created_at = datetime.strptime(
                repo["createdAt"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)

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

    def set_repo_topics(self, org, repo, topics):
        path_segments = [
            "repos",
            org,
            repo,
            "topics",
        ]
        url = self._url(path_segments)

        payload = {
            "names": topics,
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._put(url, headers=headers, json=payload)

        r.raise_for_status()

        return r.json()


def _get_github_api():
    """Simple invocation wrapper of GitHubAPI"""
    return GitHubAPI(_session=session, token=GITHUB_TOKEN)  # pragma: no cover
