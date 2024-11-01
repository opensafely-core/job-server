import textwrap
from datetime import UTC, datetime

from django.utils import timezone

from jobserver.github import GitHubError


class FakeGitHubAPI:
    """Fake GitHubAPI that returns reasonable values for each corresponding
    public function."""

    def add_repo_to_team(self, team, org, repo):
        return

    def create_issue(self, org, repo, title, body, labels):
        return {
            "html_url": "http://example.com",
        }

    def get_issue_number_from_title(
        self, org, repo, title_text, latest=True, state=None
    ):
        return 1

    def create_issue_comment(
        self, org, repo, title_text, body, latest=True, issue_number=None
    ):
        return {
            "html_url": "http://example.com/issues/comment",
        }

    def close_issue(self, org, repo, title_text, comment=None, latest=True):
        return {
            "html_url": "http://example.com/issues/comment",
        }

    def create_repo(self, org, repo):
        return {
            "html_url": "http://example.com",
            "topics": [],
        }

    def get_branch(self, org, repo, branch):
        return {
            "commit": {
                "sha": "abc123",
            }
        }

    def get_branches(self, org, repo):
        return [
            {
                "name": "test",
            },
        ]

    def get_branch_sha(self, org, repo, branch):
        return self.get_branch(org, repo, branch)["commit"]["sha"]

    def get_tag_sha(self, org, repo, tag):
        return "test_sha"

    def get_file(self, org, repo, branch, filepath="project.yaml"):
        return textwrap.dedent(
            """
            actions:
              frobnicate:
            """
        )

    def get_repo(self, org, repo):
        return {
            "created_at": "2020-07-31T13:37:00Z",
            "html_url": "http://example.com",
            "topics": ["github-releases"],
            "private": True,
        }

    def get_repo_is_private(self, org, repo):
        return self.get_repo(org, repo)["private"]

    def get_repos_with_branches(self, org):
        return [
            {
                "name": "test",
                "url": "test",
                "branches": ["main"],
            },
        ]

    def get_repos_with_dates(self, org):
        return [
            {
                "name": "predates-job-server",
                "url": "https://github.com/opensafely/predates-job-server",
                "is_private": True,
                "created_at": datetime(2020, 7, 31, tzinfo=UTC),
                "topics": ["github-releases"],
            },
            {
                "name": "research-repo-1",
                "url": "https://github.com/opensafely/research-repo-1",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": ["github-releases"],
            },
            {
                "name": "research-repo-2",
                "url": "https://github.com/opensafely/research-repo-2",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": [],
            },
            {
                "name": "research-repo-3",
                "url": "https://github.com/opensafely/research-repo-3",
                "is_private": False,
                "created_at": timezone.now(),
                "topics": ["github-releases"],
            },
            {
                "name": "no workspaces or jobs",
                "url": "https://github.com/opensafely/research-repo-4",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": [],
            },
            {
                "name": "jobs haven't run",
                "url": "https://github.com/opensafely/research-repo-5",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": [],
            },
        ]

    def get_repos_with_status_and_url(self, orgs):
        return [
            {
                "is_private": True,
                "url": "https://github.com/opensafely/research-repo-1",
            },
            {
                "is_private": True,
                "url": "https://github.com/opensafely/research-repo-2",
            },
            {
                "is_private": False,
                "url": "https://github.com/opensafely/research-repo-3",
            },
            {
                "is_private": True,
                "url": "https://github.com/opensafely/research-repo-4",
            },
            {
                "is_private": True,
                "url": "https://github.com/opensafely/research-repo-5",
            },
        ]

    def set_repo_topics(self, org, repo, topics):
        return {
            "names": [],
        }


class FakeGitHubAPIWithErrors:
    """Fake GitHubAPI that returns an error for each corresponding public
    function."""

    def add_repo_to_team(self, team, org, repo):
        raise GitHubError()

    def create_issue(self, org, repo, title, body, labels):
        # Some unit tests want to check the message.
        raise GitHubError("An error occurred")

    def get_issue_number_from_title(
        self, org, repo, title_text, latest=True, state=None
    ):
        raise GitHubError()

    def create_issue_comment(
        self, org, repo, title_text, body, latest=True, issue_number=1
    ):
        # Some unit tests want to check the message.
        raise GitHubError("An error occurred")

    def close_issue(self, org, repo, title_text, comment=None, latest=True):
        # Some unit tests want to check the message.
        raise GitHubError("An error occurred")

    def create_repo(self, org, repo):
        raise GitHubError()

    def get_branch(self, org, repo, branch):
        raise GitHubError()

    def get_branches(self, org, repo):
        raise GitHubError()

    def get_branch_sha(self, org, repo, branch):
        raise GitHubError()

    def get_tag_sha(self, org, repo, tag):
        raise GitHubError()

    def get_file(self, org, repo, branch, filepath="project.yaml"):
        raise GitHubError()

    def get_repo(self, org, repo):
        raise GitHubError()

    def get_repo_is_private(self, org, repo):
        raise GitHubError()

    def get_repos_with_branches(self, org):
        raise GitHubError()

    def get_repos_with_dates(self, org):
        raise GitHubError()

    def get_repos_with_status_and_url(self, orgs):
        raise GitHubError()

    def set_repo_topics(self, org, repo, topics):
        raise GitHubError()


class FakeOpenCodelistsAPI:
    def get_codelists(self, coding_system):
        return [
            {
                "slug": "bennett/event-codelist/event123",
                "name": "Event Codelist",
                "organisation": "Bennett Institute",
                "updated_date": "2021-07-01",
            },
            {
                "slug": "bennett/medication-codelist/medication123",
                "name": "Medication Codelist",
                "organisation": "Bennett Institute",
                "updated_date": "2022-11-09",
            },
        ]

    def check_codelists(self, txt_content, json_content):
        return {"status": "ok"}
