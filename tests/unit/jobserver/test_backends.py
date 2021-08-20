import pytest
from django.utils import timezone

from jobserver.backends import (
    backends_to_choices,
    get_configured_backends,
    show_warning,
)

from ...factories import BackendFactory
from ...utils import minutes_ago


@pytest.mark.django_db
def test_backends_to_choices():
    b1 = BackendFactory(slug="test1", name="Display One")
    b2 = BackendFactory(slug="test2", name="Display Two")

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
    monkeypatch.setenv("BACKENDS", "tpp,dog,expectations")

    with pytest.raises(Exception, match="Unknown backends: dog"):
        get_configured_backends()


def test_show_warning_last_seen_is_none():
    assert show_warning(None) is False


def test_show_warning_last_seen_equal_threhold(freezer):
    last_seen = minutes_ago(timezone.now(), 3)
    assert show_warning(last_seen, minutes=3) is True


def test_show_warning_last_seen_less_than_threhold(freezer):
    last_seen = minutes_ago(timezone.now(), 2)
    assert show_warning(last_seen, minutes=3) is False


def test_show_warning_success(freezer):
    last_seen = minutes_ago(timezone.now(), 6)
    assert show_warning(last_seen) is True
