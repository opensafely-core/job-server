import textwrap
from datetime import datetime, timezone

from django.utils.timezone import now


class FakeGitHubAPI:
    def create_issue(self, org, repo, title, body, labels):
        return {
            "html_url": "http://example.com",
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

    def get_commits(self, org, repo):
        return [
            {
                "commit": {
                    "tree": {"sha": "abc123"},
                    "message": "I am a short message title\n\nI am the message body",
                },
            }
        ]

    def get_file(self, org, repo, branch):
        return textwrap.dedent(
            """
            actions:
              frobnicate:
            """
        )

    def get_repo(self, org, repo):
        return {
            "created_at": "2020-07-31T13:37:00Z",
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
                "created_at": datetime(2020, 7, 31, tzinfo=timezone.utc),
                "topics": ["github-releases"],
            },
            {
                "name": "research-repo-1",
                "url": "https://github.com/opensafely/research-repo-1",
                "is_private": True,
                "created_at": now(),
                "topics": ["github-releases"],
            },
            {
                "name": "research-repo-2",
                "url": "https://github.com/opensafely/research-repo-2",
                "is_private": True,
                "created_at": now(),
                "topics": [],
            },
            {
                "name": "research-repo-3",
                "url": "https://github.com/opensafely/research-repo-3",
                "is_private": False,
                "created_at": now(),
                "topics": ["github-releases"],
            },
            {
                "name": "no workspaces or jobs",
                "url": "https://github.com/opensafely/research-repo-4",
                "is_private": True,
                "created_at": now(),
                "topics": [],
            },
            {
                "name": "jobs haven't run",
                "url": "https://github.com/opensafely/research-repo-5",
                "is_private": True,
                "created_at": now(),
                "topics": [],
            },
        ]


class FakeOpenCodelistsAPI:
    def get_codelists(self, coding_system):
        return [
            {
                "slug": "bennett/event-codelist/event123",
                "name": "Event Codelist",
                "organisation": "Bennett Institute",
            },
            {
                "slug": "bennett/medication-codelist/medication123",
                "name": "Medication Codelist",
                "organisation": "Bennett Institute",
            },
        ]
