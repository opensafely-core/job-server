import pytest

from jobserver.github import (
    GitHubAPI,
    _iter_query_results,
    get_repos_with_branches,
    get_repos_with_dates,
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
