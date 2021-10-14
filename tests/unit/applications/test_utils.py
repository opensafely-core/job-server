import pytest

from applications.utils import value_for_presentation


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "Yes"),
        (False, "No"),
        (None, ""),
        ("test", "test"),
    ],
)
def test_value_for_presentation(value, expected):
    assert value_for_presentation(value) == expected
