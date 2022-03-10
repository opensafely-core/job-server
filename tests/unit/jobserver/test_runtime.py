import pytest

from jobserver.runtime import Runtime, less_than_60


def test_lessthan60_success():
    output = less_than_60(None, "an_attribute", 20)

    assert output is None


def test_lessthan60_failure():
    with pytest.raises(ValueError):
        less_than_60(None, "an_attribute", 61)


def test_runtime_bool():
    assert Runtime(1, 3, 42)

    assert not Runtime(0, 0, 0)


def test_runtime_defaults():
    runtime = Runtime()

    assert runtime.hours == 0
    assert runtime.minutes == 0
    assert runtime.seconds == 0
    assert runtime.total_seconds == 0


def test_runtime_str_success():
    r = Runtime(hours=1, minutes=37, seconds=12)

    assert str(r) == "01:37:12"


def test_runtime_str_with_zero_runtime():
    assert str(Runtime(0, 0, 0)) == "-"


def test_runtime_validation():
    with pytest.raises(ValueError):
        Runtime(hours=1, minutes=62, seconds=3)
