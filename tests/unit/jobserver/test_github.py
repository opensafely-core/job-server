import pytest
import requests

from jobserver.github import (
    GitHubAPI,
    _iter_query_results,
    get_branch,
    get_branch_sha,
    get_file,
    get_repo,
    get_repo_is_private,
    get_repos_with_branches,
    get_repos_with_dates,
    is_member_of_org,
)


@pytest.mark.parametrize(
    "parts,query_args,expected",
    [
        ([], None, ""),
        ([], {"key": "value"}, "?key=value"),
        (["path", "to", "page"], None, "/path/to/page"),
        (
            ["path", "to", "page"],
            {"key": "value"},
            "/path/to/page?key=value",
        ),
    ],
)
def test_githubapi_url(parts, query_args, expected):
    api = GitHubAPI(_session=None)

    assert api._url(parts, query_args) == f"https://api.github.com{expected}"


def test_get_branch(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo/branches/main"
    responses.add(responses.GET, expected_url, json={"test": "test"}, status=200)

    output = get_branch("opensafely", "some_repo", "main")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert call.response.text == '{"test": "test"}'

    assert output == {"test": "test"}


def test_get_branch_with_missing_branch(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo/branches/main"
    responses.add(responses.GET, expected_url, status=404)

    output = get_branch("opensafely", "some_repo", "main")

    assert len(responses.calls) == 1
    assert output is None


def test_get_branch_sha(mocker):
    data = {
        "commit": {
            "sha": "abc123",
        }
    }
    mocker.patch("jobserver.github.get_branch", autospec=True, return_value=data)

    output = get_branch_sha("opensafely", "some_repo", "main")

    assert output == "abc123"


def test_get_branch_sha_with_missing_branch(mocker):
    mocker.patch("jobserver.github.get_branch", autospec=True, return_value=None)

    output = get_branch_sha("opensafely", "some_repo", "main")

    assert output is None


def test_get_file(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo/contents/project.yaml?ref=main"
    responses.add(responses.GET, expected_url, body="a file!", status=200)

    get_file("opensafely", "some_repo", "main")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.3.raw"

    assert call.response.text == "a file!"


def test_get_file_missing_project_yml(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo/contents/project.yaml?ref=missing_project"
    responses.add(responses.GET, expected_url, status=404)

    output = get_file("opensafely", "some_repo", "missing_project")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.3.raw"

    assert output is None


def test_get_repo(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo"
    responses.add(responses.GET, expected_url, json={"test": "test"}, status=200)

    output = get_repo("opensafely", "some_repo")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert call.response.text == '{"test": "test"}'

    assert output == {"test": "test"}


def test_get_repo_is_private(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo"
    responses.add(responses.GET, expected_url, json={"private": True}, status=200)

    is_private = get_repo_is_private("opensafely", "some_repo")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert call.response.text == '{"private": true}'

    assert is_private


def test_get_repo_is_private_with_unknown_repo(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo"
    responses.add(responses.GET, expected_url, status=404)

    is_private = get_repo_is_private("opensafely", "some_repo")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"

    assert is_private is None


def test_get_repo_with_unknown_repo(responses):
    expected_url = "https://api.github.com/repos/opensafely/some_repo"
    responses.add(responses.GET, expected_url, status=404)

    output = get_repo("opensafely", "some_repo")

    assert len(responses.calls) == 1

    call = responses.calls[0]

    # check the headers are correct
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"

    assert output is None


def test_get_repos_with_branches(responses):
    def data(hasNextPage):
        return {
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
                            ],
                            "pageInfo": {
                                "endCursor": "test-cursor",
                                "hasNextPage": hasNextPage,
                            },
                        }
                    }
                }
            }
        }

    expected_url = "https://api.github.com/graphql"
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=True), status=200
    )
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=False), status=200
    )

    output = list(get_repos_with_branches("opensafely"))

    assert len(responses.calls) == 2

    assert len(output) == 2
    assert output[0]["name"] == "test-repo"
    assert output[0]["branches"][0] == "branch1"


def test_get_repos_with_dates(responses):
    def data(hasNextPage):
        return {
            "data": {
                "organization": {
                    "team": {
                        "repositories": {
                            "nodes": [
                                {
                                    "name": "test-repo",
                                    "url": "http://example.com/test/test/",
                                    "isPrivate": True,
                                    "createdAt": "2021-10-07T13:37:00Z",
                                    "repositoryTopics": {
                                        "nodes": [
                                            {
                                                "topic": {
                                                    "name": "test",
                                                }
                                            }
                                        ]
                                    },
                                }
                            ],
                            "pageInfo": {
                                "endCursor": "test-cursor",
                                "hasNextPage": hasNextPage,
                            },
                        }
                    }
                }
            }
        }

    expected_url = "https://api.github.com/graphql"
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=True), status=200
    )
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=False), status=200
    )

    output = list(get_repos_with_dates())

    assert len(responses.calls) == 2

    assert len(output) == 2
    assert output[0]["name"] == "test-repo"
    assert output[0]["topics"] == ["test"]


def test_get_repos_with_dates_without_topics(responses):
    def data(hasNextPage):
        return {
            "data": {
                "organization": {
                    "team": {
                        "repositories": {
                            "nodes": [
                                {
                                    "name": "test-repo",
                                    "url": "http://example.com/test/test/",
                                    "isPrivate": True,
                                    "createdAt": "2021-10-07T13:37:00Z",
                                    "repositoryTopics": {
                                        "nodes": [],
                                    },
                                }
                            ],
                            "pageInfo": {
                                "endCursor": "test-cursor",
                                "hasNextPage": hasNextPage,
                            },
                        }
                    }
                }
            }
        }

    expected_url = "https://api.github.com/graphql"
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=True), status=200
    )
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=False), status=200
    )

    output = list(get_repos_with_dates())

    assert len(responses.calls) == 2

    assert len(output) == 2
    assert output[0]["name"] == "test-repo"
    assert output[0]["topics"] == []


def test_is_member_of_org_failure(monkeypatch, responses):
    monkeypatch.setenv("GITHUB_TESTING_TOKEN", "test")
    membership_url = "https://api.github.com/orgs/testing/members/dummy-user"
    responses.add(responses.GET, membership_url, status=404)

    assert not is_member_of_org("testing", "dummy-user")

    # check the headers are correct
    call = responses.calls[0]
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert not call.response.text


def test_is_member_of_org_success(monkeypatch, responses):
    monkeypatch.setenv("GITHUB_TESTING_TOKEN", "test")
    membership_url = "https://api.github.com/orgs/testing/members/dummy-user"
    responses.add(responses.GET, membership_url, status=204)

    assert is_member_of_org("testing", "dummy-user")

    # check the headers are correct
    call = responses.calls[0]
    assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
    assert not call.response.text


def test_is_member_of_org_without_github(monkeypatch, responses):
    monkeypatch.setenv("GITHUB_TESTING_TOKEN", "test")
    membership_url = "https://api.github.com/orgs/testing/members/dummy-user"
    responses.add(responses.GET, membership_url, status=401)

    with pytest.raises(requests.HTTPError):
        is_member_of_org("testing", "dummy-user")


def test_iter_query_results_200_error(responses):
    # graphql API returns errors in with a 200 response
    def data(hasNextPage):
        # example error from prod
        return {
            "errors": [
                {
                    "extensions": {
                        "argumentName": "login",
                        "code": "variableMismatch",
                        "errorMessage": "Nullability mismatch",
                        "typeName": "String",
                        "variableName": "org_name",
                    },
                    "locations": [{"column": 20, "line": 3}],
                    "message": (
                        "Nullability mismatch on variable $org_name and "
                        "argument login (String / String!)"
                    ),
                    "path": ["query reposAndBranches", "organization", "login"],
                }
            ]
        }

    expected_url = "https://api.github.com/graphql"
    responses.add(
        responses.POST, url=expected_url, json=data(hasNextPage=True), status=200
    )

    query = ""  # empty query as we're not going to execute it
    with pytest.raises(RuntimeError):
        list(_iter_query_results(query))
