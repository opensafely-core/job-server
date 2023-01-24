import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone
from first import first

from jobserver.context_processors import (
    backend_warnings,
    can_view_staff_area,
    nav,
    staff_nav,
)

from ...factories import BackendFactory, JobRequestFactory, StatsFactory, UserFactory
from ...utils import minutes_ago


def test_backend_warnings_with_debug_on(rf, settings):
    settings.DEBUG = True

    # set up some stats which should show up a warning in normal circumstances
    backend = BackendFactory(is_active=True)

    JobRequestFactory(backend=backend)

    last_seen = minutes_ago(timezone.now(), 10)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


def test_backend_warnings_with_no_warnings(rf):
    backend = BackendFactory(is_active=True)

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


def test_backend_warnings_with_warnings(rf):
    backend = BackendFactory(is_active=True)
    BackendFactory(is_active=True)

    JobRequestFactory(backend=backend)

    last_seen = minutes_ago(timezone.now(), 10)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == [backend.name]


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


def test_nav_jobs_authenticated(rf):
    request = rf.get(reverse("job-list"))
    request.user = UserFactory()

    projects, jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is True
    assert projects["is_active"] is False
    assert status["is_active"] is False


def test_nav_jobs_unauthenticated(rf):
    request = rf.get(reverse("job-list"))
    request.user = AnonymousUser()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is True
    assert status["is_active"] is False


def test_nav_projects_authenticated(rf):
    request = rf.get(reverse("your-projects"))
    request.user = UserFactory()

    projects, jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert projects["is_active"] is True
    assert status["is_active"] is False


def test_nav_status_authenticated(rf):
    request = rf.get(reverse("status"))
    request.user = UserFactory()

    projects, jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert projects["is_active"] is False
    assert status["is_active"] is True


def test_nav_status_unauthenticated(rf):
    request = rf.get(reverse("status"))
    request.user = AnonymousUser()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is True
