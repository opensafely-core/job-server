from jobserver.templatetags.querystring_tools import (
    url_with_querystring,
    url_without_querystring,
)


def test_url_with_querystring_setting_other_arg_set_with_no_page(rf):
    context = {"request": rf.get("/")}

    output = url_with_querystring(context, foo="bar")

    assert output == "/?foo=bar"


def test_url_with_querystring_setting_other_arg_when_page_equals_2(rf):
    """
    Test {% url_with_querystring foo=bar %} when the URL contains ?page=2

    We want the _addition_ of a filter query arg to the URL to remove any page
    argument
    """
    context = {"request": rf.get("/?page=2")}

    output = url_with_querystring(context, foo="bar")

    assert output == "/?foo=bar"


def test_url_with_querystring_updating_other_arg_set_and_page_equals_2(rf):
    """
    Test {% url_with_querystring foo=bar %} when the URL contains ?page=2

    We want the _addition_ of a filter query arg to the URL to remove any page
    argument
    """
    context = {"request": rf.get("/?page=2&foo=test")}

    output = url_with_querystring(context, foo="bar")

    assert output == "/?foo=bar"


def test_url_with_querystring_setting_page(rf):
    context = {"request": rf.get("/")}

    output = url_with_querystring(context, page="3")

    assert output == "/?page=3"


def test_url_with_querystring_updating_page(rf):
    context = {"request": rf.get("/?page=2")}

    output = url_with_querystring(context, page="3")

    assert output == "/?page=3"


def test_url_without_querystring_setting_other_arg_set_with_no_page(rf):
    context = {"request": rf.get("/?foo=bar")}

    output = url_without_querystring(context, foo="bar")

    assert output == "/"


def test_url_without_querystring_setting_other_arg_when_page_equals_2(rf):
    """
    Test {% url_without_querystring foo=bar %} when the URL contains ?page=2

    We want the _addition_ of a filter query arg to the URL to remove any page
    argument
    """
    context = {"request": rf.get("/?foo=bar&page=2")}

    output = url_without_querystring(context, foo="bar")

    assert output == "/"
