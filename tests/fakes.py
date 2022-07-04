class FakeGitHubAPI:
    def get_commits(self, org, repo):
        return [
            {
                "commit": {
                    "tree": {"sha": "abc123"},
                    "message": "I am a short message title\n\nI am the message body",
                },
            }
        ]
