import responses

from jobserver.github import get_branch_sha, get_file, get_repos_with_branches


@responses.activate
def test_get_branch_sha():
    data = {
        "commit": {
            "sha": "abc123",
        }
    }

    expected_url = "https://api.github.com/repos/opensafely/some_repo/branches/master"
    responses.add(responses.GET, expected_url, json=data, status=200)

    output = get_branch_sha("some_repo", "master")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert "token" in call.request.headers["Authorization"]
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert call.response.text == '{"commit": {"sha": "abc123"}}'

    assert output == "abc123"


@responses.activate
def test_get_file():
    expected_url = "https://api.github.com/repos/opensafely/some_repo/contents/project.yaml?ref=master"
    responses.add(responses.GET, expected_url, body="a file!", status=200)

    get_file("some_repo", "master")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert "token" in call.request.headers["Authorization"]
    assert call.request.headers["Accept"] == "application/vnd.github.3.raw"

    assert call.response.text == "a file!"


@responses.activate
def test_get_file_missing_project_yml():
    expected_url = "https://api.github.com/repos/opensafely/some_repo/contents/project.yaml?ref=missing_project"
    responses.add(responses.GET, expected_url, status=404)

    output = get_file("some_repo", "missing_project")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert "token" in call.request.headers["Authorization"]
    assert call.request.headers["Accept"] == "application/vnd.github.3.raw"

    assert output is None


@responses.activate
def test_get_repos_with_branches():
    data = {
        "data": {
            "organization": {
                "team": {
                    "repositories": {
                        "nodes": [
                            {
                                "name": "test-repo",
                                "url": "http://example.com/test/test/",
                                "refs": {
                                    "nodes": [
                                        {"name": "branch1"},
                                        {"name": "branch2"},
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        }
    }
    expected_url = "https://api.github.com/graphql"
    responses.add(responses.POST, url=expected_url, json=data, status=200)

    output = list(get_repos_with_branches())

    assert len(responses.calls) == 1

    # check the headers are correct
    assert "bearer" in responses.calls[0].request.headers["Authorization"]

    assert len(output) == 1
    assert output[0]["name"] == "test-repo"
    assert output[0]["branches"][0] == "branch1"
