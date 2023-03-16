from staff.querystring_tools import get_next_url


def test_get_next_url_with_empty_next_url_and_a_default():
    assert get_next_url({"next": []}, default="/default/") == "/default/"


def test_get_next_url_with_next_url_and_default():
    url = get_next_url({"next": ["/next/page/"]}, default="/default/")
    assert url == "/next/page/"


def test_get_next_url_with_no_next_url_and_a_default():
    assert get_next_url({}, default="/default/") == "/default/"


def test_get_next_url_with_no_next_url_and_no_default():
    assert get_next_url({}) == ""
