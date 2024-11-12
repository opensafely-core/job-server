import json
from datetime import UTC, datetime

import requests
import structlog
from django.conf import settings
from environs import Env
from furl import furl


logger = structlog.getLogger(__name__)

env = Env()


JOBSERVER_GITHUB_TOKEN = env.str("JOBSERVER_GITHUB_TOKEN")


session = requests.Session()
session.headers = {
    "User-Agent": "OpenSAFELY Jobs",
}

# Clients should catch GitHubError to handle common, often transient, connection
# issues gracefully. Some HTTPError status codes indicate specific API errors
# related to remote state (e.g., attempting to create an object that already
# exists). These cases should raise specific HTTPError exceptions from this
# module, allowing clients to handle such errors without relying on internal
# implementation details.


class GitHubError(Exception):
    """Base exception for this module. A problem contacting or using the GitHub
    API."""


class Timeout(GitHubError):
    """A request to the GitHub API timed out."""


class ConnectionException(GitHubError):
    """A connection error occurred while contacting the GitHub API."""

    # ConnectionError is a Python default exception class, so let's avoid using
    # that name. Otherwise we might have mirrored the name of
    # requests.exceptions.ConnectionError.


class HTTPError(GitHubError):
    """An HTTP request with an error status code was returned by the GitHub
    API."""


class RepoAlreadyExists(HTTPError):
    """Tried to create a repo that already existed."""


class RepoNotYetCreated(HTTPError):
    """Tried to delete a repo that did not already exist."""


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
        Initialise the wrapper with a session and maybe token.

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
        Make a request to the remote GitHub API.

        A wrapper for `requests.Session.request` that injects an
        `Authorization` header if a token is set on the API instance and not
        already included in the request headers.

        This design allows for instance-level authentication with different
        tokens (e.g., for production, CI verification tests, or unauthenticated
        queries) without setting the header globally on the session.

        Raises locally-defined Exceptions for common connection errors.
        """
        headers = kwargs.pop("headers", {})

        if self.token and "Authorization" not in headers:
            headers = headers | {"Authorization": f"bearer {self.token}"}

        try:
            return self.session.request(method, *args, headers=headers, **kwargs)
        except requests.Timeout as exc:
            raise Timeout(exc)
        except requests.ConnectionError as exc:
            raise ConnectionException(exc)

    def _raise_for_status(self, request):
        try:
            request.raise_for_status()
        except requests.HTTPError as exc:
            raise HTTPError(exc)

    def _get_query_page(self, *, query, session, cursor, **kwargs):
        """
        Get a page of the given query.

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

        if not r.ok:  # pragma: no cover
            print(r.headers)
            print(r.content)

        self._raise_for_status(r)
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
        Get results from a GraphQL query.

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

            # Update the cursor we pass into the GraphQL query.
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

        self._raise_for_status(r)

        return

    def create_issue(self, org, repo, title, body, labels):
        if settings.DEBUG:  # pragma: no cover
            logger.info("Issue created", title=title, org=org, repo=repo, body=body)
            print("")
            print(f"Repo: https://github.com/{org}/{repo}/")
            print(f"Title: {title}")
            print("Message:")
            print(body)
            print("")
            return {"html_url": "http://example.com"}
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

        self._raise_for_status(r)

        return r.json()

    def get_issue_number_from_title(
        self, org, repo, title_text, latest=True, state=None
    ):
        """
        Use search to find issue by title text (can be partial)
        Returns the issue number.
        By default, fetches both open and closed issues, and sorts by reverse
        created date, so if there is > 1 matching issue, returns the latest (most
        recently created issue)
        """
        path_segments = [
            "search",
            "issues",
        ]

        url = self._url(path_segments)

        query = f"org:{org} repo:{repo} in:title {title_text}"
        if state is not None:
            query += f" is:{state}"

        payload = {
            "q": query,
            "sort": "created",
            "order": "desc" if latest else "asc",
            "per_page": 1,
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._get(url, headers=headers, params=payload)

        self._raise_for_status(r)

        results = r.json()
        count = results["total_count"]
        items = results["items"]

        if count > 0:
            return items[0]["number"]

    def create_issue_comment(
        self, org, repo, title_text, body, latest=True, issue_number=None
    ):
        if settings.DEBUG:  # pragma: no cover
            logger.info(
                "Issue comment created",
                title_text=title_text,
                org=org,
                repo=repo,
                body=body,
            )
            print("")
            print(f"Repo: https://github.com/{org}/{repo}/")
            print(f"Title text: {title_text}")
            print("Comment:")
            print(body)
            print("")
            return {"html_url": "http://example.com/issues/comment"}

        if issue_number is None:
            issue_number = self.get_issue_number_from_title(
                org, repo, title_text, latest
            )

        path_segments = ["repos", org, repo, "issues", issue_number, "comments"]
        url = self._url(path_segments)

        payload = {
            "body": body,
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._post(url, headers=headers, json=payload)

        self._raise_for_status(r)

        return r.json()

    def _change_issue_state(self, org, repo, issue_number, to_state):
        path_segments = ["repos", org, repo, "issues", issue_number]
        payload = {"state": to_state}
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        url = self._url(path_segments)
        r = self._post(url, headers=headers, json=payload)

        self._raise_for_status(r)

    def close_issue(self, org, repo, title_text, comment=None, latest=True):
        if settings.DEBUG:  # pragma: no cover
            logger.info(
                "Issue closed",
                title_text=title_text,
                comment=comment,
                org=org,
                repo=repo,
            )
            print("")
            print(f"Repo: https://github.com/{org}/{repo}/")
            print(f"Title text: {title_text}")
            print("")
            return {"html_url": "http://example.com/issues/closed"}

        issue_number = self.get_issue_number_from_title(
            org, repo, title_text, latest, state="open"
        )
        r = self._change_issue_state(org, repo, issue_number, "closed")

        path_segments = ["repos", org, repo, "issues", issue_number]
        url = self._url(path_segments)

        payload = {
            "state": "closed",
        }

        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        r = self._post(url, headers=headers, json=payload)

        self._raise_for_status(r)

        if comment is not None:
            self.create_issue_comment(
                org, repo, title_text, comment, issue_number=issue_number
            )

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
        if r.status_code == 422:
            raise RepoAlreadyExists()

        self._raise_for_status(r)

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

        if not r.ok:
            print(r.headers)
            print(r.content)

        if r.status_code == 403:
            # It's possible for us to create and then attempt to delete a repo
            # faster than GitHub can create it on disk, so lets wait and retry
            # if that's happened.
            # Note: 403 isn't just used for this state.
            msg = "Repository cannot be deleted until it is done being created on disk."
            if msg in r.json().get("message", ""):
                raise RepoNotYetCreated()

        self._raise_for_status(r)

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

        self._raise_for_status(r)

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

        self._raise_for_status(r)

        return r.json()

    def get_branch_sha(self, org, repo, branch):
        branch = self.get_branch(org, repo, branch)

        if branch is None:
            return

        return branch["commit"]["sha"]

    def get_tag_sha(self, org, repo, tag):
        path_segments = ["repos", org, repo, "git", "refs", "tags", tag]
        url = self._url(path_segments)
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }

        r = self._get(url, headers=headers)
        self._raise_for_status(r)

        return r.json()["object"]["sha"]

    def get_file(self, org, repo, branch, filepath="project.yaml"):
        path_segments = [
            "repos",
            org,
            repo,
            "contents",
            filepath,
        ]
        query_args = {"ref": branch}
        url = self._url(path_segments, query_args)

        headers = {
            "Accept": "application/vnd.github.3.raw",
        }
        r = self._get(url, headers=headers)

        if r.status_code == 404:
            return

        self._raise_for_status(r)

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

        self._raise_for_status(r)

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
                topics = [
                    n["topic"]["name"]
                    for n in repo["repositoryTopics"]["nodes"]
                    if n is not None
                ]

            if "non-research" in topics:
                continue  # Ignore non-research repos.

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
            ).replace(tzinfo=UTC)

            topics = []
            if repo["repositoryTopics"]["nodes"]:
                topics = [
                    n["topic"]["name"]
                    for n in repo["repositoryTopics"]["nodes"]
                    if n is not None
                ]

            yield {
                "name": repo["name"],
                "url": repo["url"],
                "is_private": repo["isPrivate"],
                "created_at": created_at,
                "topics": topics,
            }

    def get_repos_with_status_and_url(self, orgs):
        query = """
        query reposWithStatusAndURL($cursor: String, $org_name: String!) {
          organization(login: $org_name) {
            repositories(first: 100, after: $cursor) {
              nodes {
                url
                isPrivate
              }
              pageInfo {
                  endCursor
                  hasNextPage
              }
            }
          }
        }
        """
        for org in orgs:
            results = list(self._iter_query_results(query, org_name=org))
            for repo in results:
                yield {
                    "is_private": repo["isPrivate"],
                    "url": repo["url"],
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

        self._raise_for_status(r)

        return r.json()


def _get_github_api():
    """Simple invocation wrapper of GitHubAPI"""
    return GitHubAPI(_session=session, token=JOBSERVER_GITHUB_TOKEN)  # pragma: no cover
