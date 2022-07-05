import textwrap
from datetime import datetime

from django.utils import timezone


class FakeGitHubAPI:
    def get_branch(self, org, repo, branch):
        return {
            "commit": {
                "sha": "abc123",
            }
        }

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

    def get_repos_with_dates(self):
        return [
            {
                "name": "job-runner",
                "url": "https://github.com/opensafely-core/job-runner",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": ["test"],
            },
            {
                "name": "job-server",
                "url": "https://github.com/opensafely-core/job-server",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": ["test"],
            },
            {
                "name": "test",
                "url": "test",
                "is_private": True,
                "created_at": timezone.now(),
                "topics": ["test"],
            },
            {
                "name": "predates-job-server",
                "url": "test-url",
                "is_private": True,
                "created_at": datetime(2020, 7, 31, tzinfo=timezone.utc),
                "topics": [],
            },
        ]
