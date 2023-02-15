import requests
from furl import furl


session = requests.Session()
session.headers = {
    "User-Agent": "OpenSAFELY Jobs",
}


class OpenCodelistsAPI:
    """
    A thin wrapper around requests, furl, and the OpenCodelists API.

    Initialising this class with a token will set that token in the sessions
    headers.

    "public" functions should construct a URL and make requests against the
    session object attached to the instance.

    This object is not expected to be used in most tests so we can avoid mocking.
    """

    base_url = "https://www.opencodelists.org/api/v1"

    def __init__(self, _session=session):
        """
        Initialise the wrapper with a session

        We pass in the session here so that tests can pass in a fake object to
        test internals.
        """
        self.session = _session

    def _url(self, path_segments, query_args=None):
        f = furl(self.base_url)

        f.path.segments += path_segments

        if query_args:
            f.add(query_args)

        return f.url

    def _iter_codelists(self, codelists):
        for codelist in codelists:
            versions = [v for v in codelist["versions"] if v["status"] == "published"]

            if not versions:
                continue

            latest = versions[-1]

            yield {
                "slug": latest["full_slug"],
                "name": codelist["name"],
                "organisation": codelist["organisation"],
            }

    def get_codelist(self, slug):
        url = furl("https://www.opencodelists.org") / "codelist" / slug / "download.csv"
        url.args["fixed-headers"] = 1
        r = requests.get(url)
        r.raise_for_status()

        return r.text

    def get_codelists(self, coding_system):
        path_segments = [
            "codelist",
        ]
        query_args = {
            "coding_system_id": coding_system,
        }
        url = self._url(path_segments, query_args)

        r = self.session.get(url)
        r.raise_for_status()

        data = self._iter_codelists(r.json()["codelists"])
        return list(sorted(data, key=lambda c: c["name"].lower()))


def _get_opencodelists_api():
    """Simple invocation wrapper of OpenCodelistsAPI"""
    return OpenCodelistsAPI(_session=session)  # pragma: no cover
