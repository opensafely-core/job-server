from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.backends import get_configured_backends, show_warning


def test_get_configured_backends_empty(monkeypatch):
    monkeypatch.setenv("BACKENDS", "")
    backends = get_configured_backends()

    assert backends == set()


def test_get_configured_backends_space_around_comma(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp , expectations")
    backends = get_configured_backends()

    assert backends == {"expectations", "tpp"}


def test_get_configured_backends_success(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp,expectations")
    backends = get_configured_backends()

    assert backends == {"expectations", "tpp"}


def test_get_configured_backends_unknown_backend(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp,test,expectations")

    with pytest.raises(Exception, match="Unknown backends: test"):
        get_configured_backends()


def test_show_warning_last_seen_is_none():
    assert show_warning(None) is False


def test_show_warning_last_seen_equal_threhold(freezer):
    last_seen = timezone.now() - timedelta(minutes=3)
    assert show_warning(last_seen, minutes=3) is True


def test_show_warning_last_seen_less_than_threhold(freezer):
    last_seen = timezone.now() - timedelta(minutes=2)
    assert show_warning(last_seen, minutes=3) is False


def test_show_warning_success(freezer):
    last_seen = timezone.now() - timedelta(minutes=6)
    assert show_warning(last_seen) is True
