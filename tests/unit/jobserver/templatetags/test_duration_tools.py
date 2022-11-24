from datetime import timedelta

import pytest

from jobserver.templatetags.duration_tools import duration


def test_duration_empty_timedelta():
    assert duration(None) == "-"
    assert duration(timedelta(seconds=0)) == "-"


@pytest.mark.parametrize(
    "delta,output",
    [
        (
            timedelta(days=5, hours=3, minutes=57, seconds=42),
            "5 days 3 hours 57 minutes 42 seconds",
        ),
        (timedelta(days=12), "12 days"),
        (timedelta(hours=7), "7 hours"),
        (timedelta(minutes=42), "42 minutes"),
        (timedelta(seconds=12), "12 seconds"),
    ],
)
def test_duration_success(delta, output):
    assert duration(delta) == output
    assert duration(None) == "-"
    assert duration(timedelta(seconds=0)) == "-"
