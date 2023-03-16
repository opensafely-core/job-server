from staff.htmx_tools import get_redirect_url


def test_get_redirect_url(rf):
    request = rf.get("/?next=/next/page/&one-arg=value")

    url = get_redirect_url(request.GET, "/default/", {"two-arg": "value"})

    assert url == "/next/page/?one-arg=value&two-arg=value"
