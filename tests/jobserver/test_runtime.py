import pytest

from jobserver.runtime import Runtime, less_than_60


def test_lessthan60_success():
    output = less_than_60(None, "an_attribute", 20)

    assert output is None


def test_lessthan60_failure():
    with pytest.raises(ValueError):
        less_than_60(None, "an_attribute", 61)


def test_runtime_defaults():
    runtime = Runtime()

    assert runtime.hours == 0
    assert runtime.minutes == 0
    assert runtime.seconds == 0
    assert runtime.total_seconds == 0


def test_runtime_validation():
    with pytest.raises(ValueError):
        Runtime(hours=1, minutes=62, seconds=3)
