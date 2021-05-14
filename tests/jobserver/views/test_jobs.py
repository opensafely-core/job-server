from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse

from jobserver.views.jobs import JobCancel, JobDetail

from ...factories import JobFactory, JobRequestFactory, UserFactory, WorkspaceFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_cancelled(rf):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_finished(rf):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="finished")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")

    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unauthorized(rf):
    job = JobFactory(job_request=JobRequestFactory())
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unknown_job(rf):
    user = UserFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    membership_url = f"https://api.github.com/orgs/opensafely/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier="not-real")


@pytest.mark.django_db
def test_jobdetail_with_authenticated_user(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=False, roles=[])

    with patch("jobserver.views.jobs.can_run_jobs", return_value=True):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_post_jobrequest_job(rf):
    job = JobFactory()

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    with patch("jobserver.views.jobs.can_run_jobs", return_value=False):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_pre_jobrequest_job(rf):
    job_request = JobRequestFactory(workspace=WorkspaceFactory())
    job = JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    with patch("jobserver.views.jobs.can_run_jobs", return_value=False):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_unauthenticated_user(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    with patch("jobserver.views.jobs.can_run_jobs", return_value=False):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="test")
