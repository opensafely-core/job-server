from staff.querystring_tools import merge_query_args


def test_merge_query_args(rf):
    request = rf.get("/?one-arg=value&two-arg=value")

    f = merge_query_args(request.GET, {"three-arg": "value"})
    assert f.args == {"one-arg": "value", "two-arg": "value", "three-arg": "value"}
