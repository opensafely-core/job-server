import pytest

from jobserver.github import GitHubAPI


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
