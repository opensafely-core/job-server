from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse

from jobserver.views.jobs import JobCancel, JobDetail, JobZombify

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
    assert "Zombify" not in response.rendered_content


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
def test_jobdetail_with_superuser(rf, superuser):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with patch("jobserver.views.jobs.can_run_jobs", return_value=True):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200
    assert "Zombify" in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_unauthenticated_user(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    with patch("jobserver.views.jobs.can_run_jobs", return_value=False):
        response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200
    assert "Zombify" not in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="test")


@pytest.mark.django_db
def test_jobzombify_not_superuser(client):
    job = JobFactory(completed_at=None)

    client.force_login(UserFactory(roles=[]))
    with patch("jobserver.views.jobs.can_run_jobs", return_value=False):
        response = client.post(f"/jobs/{job.identifier}/zombify/", follow=True)

    assert response.status_code == 200

    # did we redirect to the correct JobDetail page?
    url = reverse("job-detail", kwargs={"identifier": job.identifier})
    assert response.redirect_chain == [(url, 302)]

    # has the Job been left untouched?
    job.refresh_from_db()
    assert job.status == ""
    assert job.status_message == ""

    # did we produce a message?
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Only admins can zombify Jobs."


@pytest.mark.django_db
def test_jobzombify_success(rf, superuser):
    job = JobFactory(completed_at=None)

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    response = JobZombify.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job.refresh_from_db()

    assert job.status == "failed"
    assert job.status_message == "Job manually zombified"


@pytest.mark.django_db
def test_jobzombify_unknown_job(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        JobZombify.as_view()(request, identifier="")
