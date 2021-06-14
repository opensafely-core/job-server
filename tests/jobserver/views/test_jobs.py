import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse

from jobserver.views.jobs import JobCancel, JobDetail

from ...factories import JobFactory, JobRequestFactory, UserFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_cancelled(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_already_finished(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="finished")

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_success(rf, user):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == reverse("job-detail", kwargs={"identifier": job.identifier})

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unauthorized(rf, user):
    job = JobFactory(job_request=JobRequestFactory())

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_jobcancel_unknown_job(rf, user):
    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier="not-real")


@pytest.mark.django_db
def test_jobdetail_with_authenticated_user(rf, mocker):
    job = JobFactory()

    mocker.patch("jobserver.views.jobs.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory(is_superuser=False, roles=[])

    response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_partial_identifier_failure(rf, mocker):
    JobFactory(identifier="123abc")
    JobFactory(identifier="123def")

    mocker.patch("jobserver.views.jobs.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="123")


@pytest.mark.django_db
def test_jobdetail_with_partial_identifier_success(rf, mocker):
    job = JobFactory()

    mocker.patch("jobserver.views.jobs.can_run_jobs", autospec=True, return_value=True)

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = JobDetail.as_view()(request, identifier=job.identifier[:4])

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()


@pytest.mark.django_db
def test_jobdetail_with_unauthenticated_user(rf, mocker):
    job = JobFactory()

    mocker.patch("jobserver.views.jobs.can_run_jobs", autospec=True, return_value=False)

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    response = JobDetail.as_view()(request, identifier=job.identifier)

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(request, identifier="test")
