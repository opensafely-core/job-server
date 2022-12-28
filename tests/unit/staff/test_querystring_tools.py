from staff.querystring_tools import get_query_args, merge_query_args


def test_get_query_args(rf):
    request = rf.get("/?one-arg=value&two-arg=value")

    query_args = get_query_args(request.GET)

    assert query_args == "?one-arg=value&two-arg=value"


def test_merge_query_args(rf):
    request = rf.get("/?one-arg=value&two-arg=value")

    f = merge_query_args(request.GET, {"three-arg": "value"})
    assert f.args == {"one-arg": "value", "two-arg": "value", "three-arg": "value"}
