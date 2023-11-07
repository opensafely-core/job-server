import pytest

from jobserver.opencodelists import OpenCodelistsAPI


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
def test_opencodelistsapi_url(parts, query_args, expected):
    api = OpenCodelistsAPI(_session=None)

    output = api._url(parts, query_args)

    assert output == f"https://www.opencodelists.org/api/v1{expected}"
