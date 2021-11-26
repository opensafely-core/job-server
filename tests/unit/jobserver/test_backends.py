from django.utils import timezone

from jobserver.backends import (
    backends,
    backends_to_choices,
    ensure_backends,
    show_warning,
)
from jobserver.models import Backend

from ...factories import BackendFactory
from ...utils import minutes_ago


def test_backends_to_choices():
    b1 = BackendFactory(slug="test1", name="Display One")
    b2 = BackendFactory(slug="test2", name="Display Two")

    choices = backends_to_choices([b1, b2])

    assert choices[0] == ("test1", "Display One")
    assert choices[1] == ("test2", "Display Two")


def test_ensure_backends_existing_backends():
    BackendFactory(pk=3, name="TEST", slug="testing")

    assert Backend.objects.count() == 1

    ensure_backends()

    assert Backend.objects.count() == len(backends)

    tpp = Backend.objects.get(pk=3)
    assert tpp.name == "TPP"
    assert tpp.slug == "tpp"


def test_ensure_backends_no_backends():
    assert Backend.objects.count() == 0

    ensure_backends()

    assert Backend.objects.count() == len(backends)


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
