import pytest
import requests
import responses
from social_core.exceptions import AuthFailed

from jobserver.github import (
    GithubOrganizationOAuth2,
    get_branch_sha,
    get_file,
    get_repos_with_branches,
)


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


@responses.activate
def test_githuborganizationoauth2_user_data_404():
    expected_url = "https://api.github.com/orgs/opensafely/members/test-username"
    responses.add(responses.GET, url=expected_url, status=404)

    class DummyBackend(GithubOrganizationOAuth2):
        def _user_data(*args, **kwargs):
            return {"email": "test-email", "login": "test-username"}

    with pytest.raises(AuthFailed, match="User doesn't belong to the organization"):
        DummyBackend().user_data("access-token")


@responses.activate
def test_githuborganizationoauth2_user_data_302():
    expected_url = "https://api.github.com/orgs/opensafely/members/test-username"
    responses.add(responses.GET, url=expected_url, status=302)

    class DummyBackend(GithubOrganizationOAuth2):
        def _user_data(*args, **kwargs):
            return {"email": "test-email", "login": "test-username"}

    DummyBackend().user_data("access-token")


@responses.activate
def test_githuborganizationoauth2_user_data_204():
    expected_url = "https://api.github.com/orgs/opensafely/members/test-username"
    responses.add(responses.GET, url=expected_url, status=204)

    class DummyBackend(GithubOrganizationOAuth2):
        def _user_data(*args, **kwargs):
            return {"email": "test-email", "login": "test-username"}

    DummyBackend().user_data("access-token")

    assert len(responses.calls) == 1


def test_githuborganizationoauth2_user_data_204_via_error():
    """
    Check an HTTPError with response.status_code == 204 doesn't throw an error

    GithubMemberOAuth2 has a check to confirm the status_code of an HTTPError
    isn't 204.  Since raise_for_status only fires on unsuccessful codes (<400)
    it's tricky to test this condition!
    """

    class DummyBackend(GithubOrganizationOAuth2):
        def _user_data(self, *args, **kwargs):
            return {"email": "test-email", "login": "test-username"}

        def request(self, *args, **kwargs):
            response = requests.Response()
            response.status_code = 204
            raise requests.exceptions.HTTPError(response=response)

    DummyBackend().user_data("access-token")
