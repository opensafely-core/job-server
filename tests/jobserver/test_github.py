import responses

from jobserver.github import get_file


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
