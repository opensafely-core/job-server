from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.backends import (
    backends_to_choices,
    get_configured_backends,
    show_warning,
)

from ..factories import BackendFactory


@pytest.mark.django_db
def test_backends_to_choices():
    b1 = BackendFactory(name="test1", display_name="Display One")
    b2 = BackendFactory(name="test2", display_name="Display Two")

    choices = backends_to_choices([b1, b2])

    assert choices[0] == ("test1", "Display One")
    assert choices[1] == ("test2", "Display Two")


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
