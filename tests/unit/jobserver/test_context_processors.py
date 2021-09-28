import pytest
from django.urls import reverse
from django.utils import timezone
from first import first

from jobserver.context_processors import (
    backend_warnings,
    can_view_staff_area,
    nav,
    staff_nav,
)
from jobserver.models import Backend

from ...factories import JobRequestFactory, StatsFactory, UserFactory
from ...utils import minutes_ago


def test_backend_warnings_with_debug_on(rf, settings):
    settings.DEBUG = True

    # set up some stats which should show up a warning in normal circumstances
    tpp = Backend.objects.get(slug="tpp")

    JobRequestFactory(backend=tpp)

    last_seen = minutes_ago(timezone.now(), 10)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


def test_backend_warnings_with_no_warnings(rf):
    tpp = Backend.objects.get(slug="tpp")

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


def test_backend_warnings_with_warnings(rf):
    tpp = Backend.objects.get(slug="tpp")

    JobRequestFactory(backend=tpp)

    last_seen = minutes_ago(timezone.now(), 10)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == ["TPP"]


def test_can_view_staff_area_with_core_developer(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    assert can_view_staff_area(request)["user_can_view_staff_area"]


def test_can_view_staff_area_without_core_developer(rf):
    request = rf.get("/")
    request.user = UserFactory()

    assert not can_view_staff_area(request)["user_can_view_staff_area"]


@pytest.mark.parametrize(
    ("url_name",),
    [("backend-list",), ("project-list",), ("user-list",)],
)
def test_staff_nav_selected_urls(rf, core_developer, url_name):
    url = reverse(f"staff:{url_name}")

    request = rf.get(url)
    request.user = core_developer

    nav_items = staff_nav(request)["staff_nav"]

    selected_url = first(nav_items, key=lambda u: u["url"] == url)
    assert selected_url["is_active"]

    unselected_urls = filter(lambda u: u["url"] != url, nav_items)
    assert all(u["is_active"] is False for u in unselected_urls)


def test_nav_jobs(rf):
    request = rf.get(reverse("job-list"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is True
    assert status["is_active"] is False


def test_nav_status(rf):
    request = rf.get(reverse("status"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is True
