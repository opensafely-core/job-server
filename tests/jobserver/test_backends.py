from datetime import timedelta

from django.utils import timezone

from jobserver.backends import show_warning


def test_show_warning_zero_unacked():
    assert show_warning(0, True) is False


def test_show_warning_last_seen_is_none():
    assert show_warning(1, None) is False


def test_show_warning_last_seen_equal_threhold(freezer):
    last_seen = timezone.now() - timedelta(minutes=3)
    assert show_warning(1, last_seen, minutes=3) is True


def test_show_warning_last_seen_less_than_threhold(freezer):
    last_seen = timezone.now() - timedelta(minutes=2)
    assert show_warning(1, last_seen, minutes=3) is False


def test_show_warning_success(freezer):
    last_seen = timezone.now() - timedelta(minutes=6)
    assert show_warning(1, last_seen) is True
