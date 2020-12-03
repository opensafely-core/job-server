from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.backends import build_backends, build_choices, show_warning


def test_build_backends_empty(monkeypatch):
    monkeypatch.setenv("BACKENDS", "")
    backends = build_backends()

    assert backends == set()


def test_build_backends_space_around_comma(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp , expectations")
    backends = build_backends()

    assert backends == {"expectations", "tpp"}


def test_build_backends_success(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp,expectations")
    backends = build_backends()

    assert backends == {"expectations", "tpp"}


def test_build_backends_unknown_backend(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp,test,expectations")

    with pytest.raises(Exception, match="Unknown backends: test"):
        build_backends()


def test_build_choices_empty_backends():
    assert build_choices({}) == []


def test_build_choices_success():
    choices = build_choices({"emis", "tpp"})

    assert choices == [("emis", "EMIS"), ("tpp", "TPP")]


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
