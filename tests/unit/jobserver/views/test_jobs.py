import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from jobserver.authorization import ProjectDeveloper
from jobserver.views.jobs import JobCancel, JobDetail, JobDetailRedirect

from ....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectMembershipFactory,
    UserFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_jobcancel_already_cancelled(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


@pytest.mark.django_db
def test_jobcancel_already_completed(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="succeeded")

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action"]


@pytest.mark.django_db
def test_jobcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


@pytest.mark.django_db
def test_jobcancel_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    job = JobFactory(job_request=job_request, action="test")

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


@pytest.mark.django_db
def test_jobcancel_without_permission(rf, user):
    job = JobFactory(job_request=JobRequestFactory())

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier=job.identifier)


@pytest.mark.django_db
def test_jobcancel_unknown_job(rf, user):
    request = rf.post(MEANINGLESS_URL)
    request.user = user

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier="not-real")


@pytest.mark.django_db
def test_jobdetail_with_anonymous_user(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    response = JobDetail.as_view()(
        request,
        org_slug=job.job_request.workspace.project.org.slug,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_permission(rf):
    job = JobFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=job.job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobDetail.as_view()(
        request,
        org_slug=job.job_request.workspace.project.org.slug,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)
    job = JobFactory(job_request=job_request)

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = JobDetail.as_view()(
        request,
        org_slug=job.job_request.workspace.project.org.slug,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


@pytest.mark.django_db
def test_jobdetail_with_partial_identifier_failure(rf, mocker):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, identifier="123abc")
    JobFactory(job_request=job_request, identifier="123def")

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobDetail.as_view()(
            request,
            org_slug=job_request.workspace.project.org.slug,
            project_slug=job_request.workspace.project.slug,
            workspace_slug=job_request.workspace.name,
            pk=job_request.pk,
            identifier="123",
        )


@pytest.mark.django_db
def test_jobdetail_with_partial_identifier_success(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = JobDetail.as_view()(
        request,
        org_slug=job.job_request.workspace.project.org.slug,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier[:4],
    )

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()


@pytest.mark.django_db
def test_jobdetail_with_unknown_job(rf):
    job_request = JobRequestFactory()

    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetail.as_view()(
            request,
            org_slug=job_request.workspace.project.org.slug,
            project_slug=job_request.workspace.project.slug,
            workspace_slug=job_request.workspace.name,
            pk=job_request.pk,
            identifier="test",
        )


@pytest.mark.django_db
def test_jobdetail_without_permission(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = JobDetail.as_view()(
        request,
        org_slug=job.job_request.workspace.project.org.slug,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content


@pytest.mark.django_db
def test_jobdetailredirect_success(rf):
    job = JobFactory()

    request = rf.get(MEANINGLESS_URL)

    response = JobDetailRedirect.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()


@pytest.mark.django_db
def test_jobdetailredirect_with_unknown_job(rf):
    request = rf.get(MEANINGLESS_URL)

    with pytest.raises(Http404):
        JobDetailRedirect.as_view()(request, identifier="test")
