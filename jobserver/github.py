import os

import requests
from furl import furl


BASE_URL = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
USER_AGENT = "OpenSAFELY Jobs"


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
    r.raise_for_status()

    return r.text
