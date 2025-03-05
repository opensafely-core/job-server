import pytest

from jobserver.runtime import Runtime


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


def test_runtime_hours_60():
    assert Runtime(60, 0, 0)


@pytest.mark.parametrize(
    ["hours", "minutes", "seconds", "total_seconds"],
    [
        (1, 60, 1, 0),
        (1, 1, 60, 0),
        (-1, 1, 1, 0),
        (1, -1, 1, 0),
        (1, 1, -1, 0),
        (1, 1, 1, -1),
    ],
    ids=[
        "minutes_more_than_59",
        "seconds_more_than_59",
        "negative_hours",
        "negative_minutes",
        "negative_seconds",
        "negative_total_seconds",
    ],
)
def test_runtime_validation(hours, minutes, seconds, total_seconds):
    with pytest.raises(ValueError):
        Runtime(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            total_seconds=total_seconds,
        )
