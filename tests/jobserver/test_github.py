import responses

from jobserver.github import _build_headers, get_file


def test_build_headers():
    headers = _build_headers()

    assert headers["Accept"] == "application/vnd.github.v3+json"
    assert headers["Authorization"] == "token dummy_token"
    assert headers["User-Agent"] == "OpenSAFELY Jobs"

    headers = _build_headers(accept="different accept")
    assert headers["Accept"] == "different accept"


@responses.activate
def test_get_file():
    expected_url = "https://api.github.com/repos/opensafely/some_repo/contents/project.yaml?ref=master"
    responses.add(responses.GET, expected_url, body="a file!", status=200)

    get_file("some_repo", "master")

    assert len(responses.calls) == 1

    call = responses.calls[0]
    # check the special case header is correct
    assert call.request.headers["Accept"] == "application/vnd.github.3.raw"
    assert call.response.text == "a file!"
