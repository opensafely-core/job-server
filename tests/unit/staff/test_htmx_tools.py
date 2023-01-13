from staff.htmx_tools import get_next_url, get_redirect_url


def test_get_next_url_with_empty_next_url_and_a_default():
    assert get_next_url({"next": []}, default="/default/") == "/default/"


def test_get_next_url_with_next_url_and_default():
    url = get_next_url({"next": ["/next/page/"]}, default="/default/")
    assert url == "/next/page/"


def test_get_next_url_with_no_next_url_and_a_default():
    assert get_next_url({}, default="/default/") == "/default/"


def test_get_next_url_with_no_next_url_and_no_default():
    assert get_next_url({}) == ""


def test_get_redirect_url(rf):
    request = rf.get("/?next=/next/page/&one-arg=value")

    url = get_redirect_url(request.GET, "/default/", {"two-arg": "value"})

    assert url == "/next/page/?one-arg=value&two-arg=value"
