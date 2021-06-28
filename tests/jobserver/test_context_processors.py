from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobserver.context_processors import backend_warnings, nav, scripts_attrs
from jobserver.models import Backend

from ..factories import JobRequestFactory, StatsFactory, UserFactory


@pytest.mark.django_db
def test_backend_warnings_with_debug_on(rf, settings):
    settings.DEBUG = True

    # set up some stats which should show up a warning in normal circumstances
    tpp = Backend.objects.get(name="tpp")

    JobRequestFactory(backend=tpp)

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


@pytest.mark.django_db
def test_backend_warnings_with_no_warnings(rf):
    tpp = Backend.objects.get(name="tpp")

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


@pytest.mark.django_db
def test_backend_warnings_with_warnings(rf):
    tpp = Backend.objects.get(name="tpp")

    JobRequestFactory(backend=tpp)

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(backend=tpp, api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == ["TPP"]


@pytest.mark.django_db
def test_nav_jobs(rf):
    request = rf.get(reverse("job-list"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is True
    assert status["is_active"] is False


@pytest.mark.django_db
def test_nav_status(rf):
    request = rf.get(reverse("status"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is True


@pytest.mark.django_db
def test_nav_backends(rf, core_developer):
    request = rf.get(reverse("backend-list"))
    request.user = core_developer

    jobs, status, backends, users = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is False
    assert backends["is_active"] is True
    assert users["is_active"] is False


@pytest.mark.django_db
def test_nav_users(rf, core_developer):
    request = rf.get(reverse("user-list"))
    request.user = core_developer

    jobs, status, backends, users = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is False
    assert backends["is_active"] is False
    assert users["is_active"] is True


@pytest.mark.django_db
def test_nav_without_core_developer_role(rf):
    request = rf.get(reverse("backend-list"))
    request.user = UserFactory()

    jobs, status = nav(request)["nav"]

    assert jobs["is_active"] is False
    assert status["is_active"] is False


@pytest.mark.django_db
def test_scriptsattrs_success(rf):
    request = rf.get("/")

    assert scripts_attrs(request) == {"scripts_attrs": {"nomodule": ""}}
