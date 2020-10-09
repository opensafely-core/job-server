import os

import requests
from furl import furl


BASE_URL = "https://api.github.com"

TOKEN = os.environ["GITHUB_TOKEN"]


def _build_headers(accept=None):
    if accept is None:
        accept = "application/vnd.github.v3+json"

    return {
        "Accept": accept,
        "Authorization": f"token {TOKEN}",
        "User-Agent": "OpenSAFELY Jobs",
    }


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

    headers = _build_headers(accept="application/vnd.github.3.raw")
    r = requests.get(f.url, headers=headers)
    r.raise_for_status()

    return r.text
