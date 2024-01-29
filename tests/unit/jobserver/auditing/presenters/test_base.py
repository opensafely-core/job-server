import pytest

from jobserver.auditing.presenters.base import LinkableObject


class Fake:
    name = "name field"

    def __str__(self):
        return "dummy object"

    def get_a_url(self):
        return "some url"


@pytest.mark.parametrize(
    "field,expected_str",
    [("", "dummy object"), ("name", "name field")],
    ids=["no_field", "field"],
)
@pytest.mark.parametrize(
    "link_func,expected_link",
    [("", None), ("get_a_url", "some url")],
    ids=["no_link_func", "link_func"],
)
def test_linkableobject_with_object(field, expected_str, link_func, expected_link):
    obj = LinkableObject.build(obj=Fake(), field=field, link_func=link_func)

    assert str(obj) == expected_str
    assert obj.link == expected_link


def test_linkableobject_with_string():
    obj = LinkableObject.build(obj="test")

    assert str(obj) == "test"
    assert not obj.link
