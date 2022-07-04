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
