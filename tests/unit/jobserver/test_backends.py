from datetime import timedelta

from django.utils import timezone

from jobserver.backends import backends_to_choices, show_warning

from ...factories import BackendFactory
from ...utils import minutes_ago


def test_backends_to_choices():
    b1 = BackendFactory(slug="test1", name="Display One")
    b2 = BackendFactory(slug="test2", name="Display Two")

    choices = backends_to_choices([b1, b2])

    assert choices[0] == ("test1", "Display One")
    assert choices[1] == ("test2", "Display Two")


def test_show_warning_last_seen_is_none():
    assert show_warning(None, timedelta()) is False


def test_show_warning_last_seen_equal_threhold(time_machine):
    last_seen = minutes_ago(timezone.now(), 3)
    assert show_warning(last_seen, timedelta(minutes=3)) is True


def test_show_warning_last_seen_greater_than_threshold(time_machine):
    last_seen = minutes_ago(timezone.now(), 6)
    assert show_warning(last_seen, timedelta(minutes=5)) is True


def test_show_warning_last_seen_less_than_threhold(time_machine):
    last_seen = minutes_ago(timezone.now(), 2)
    assert show_warning(last_seen, timedelta(minutes=3)) is False
