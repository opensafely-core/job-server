import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import CoreDeveloper, ProjectDeveloper
from jobserver.views.jobs import JobCancel, JobDetail, JobDetailRedirect

from ....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectMembershipFactory,
    UserFactory,
)


def test_jobcancel_already_cancelled(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


def test_jobcancel_already_completed(rf, user):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="succeeded")

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action"]


def test_jobcancel_success(rf):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")
    user = UserFactory()

    ProjectMembershipFactory(
        project=job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


def test_jobcancel_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    job = JobFactory(job_request=job_request, action="test")

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]


def test_jobcancel_without_permission(rf, user):
    job = JobFactory(job_request=JobRequestFactory())

    request = rf.post("/")
    request.user = user

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier=job.identifier)


def test_jobcancel_unknown_job(rf, user):
    request = rf.post("/")
    request.user = user

    with pytest.raises(Http404):
        JobCancel.as_view()(request, identifier="not-real")


def test_jobdetail_with_anonymous_user(rf):
    job = JobFactory()

    request = rf.get("/")
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
    assert "Honeycomb" not in response.rendered_content


def test_jobdetail_with_permission(rf):
    job = JobFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=job.job_request.workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
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
    assert "Honeycomb" not in response.rendered_content


@pytest.mark.freeze_time("2022-06-16 12:00")
def test_jobdetail_with_core_developer(rf):
    job = JobFactory()
    user = UserFactory(roles=[CoreDeveloper])

    request = rf.get("/")
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
    assert "Cancel" not in response.rendered_content
    assert "Honeycomb" in response.rendered_content
    assert "%22end_time%22%3A1655380800%2C" in response.rendered_content
    assert (
        "workspace_name%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22workspace-7"
        in response.rendered_content
    )


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_jobdetail_with_core_developer_with_completed_at(rf):
    job = JobFactory(completed_at=timezone.now())
    user = UserFactory(roles=[CoreDeveloper])

    request = rf.get("/")
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
    assert "Cancel" not in response.rendered_content
    assert "Honeycomb" in response.rendered_content
    assert "%22end_time%22%3A1655298060%2C" in response.rendered_content


def test_jobdetail_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)
    job = JobFactory(job_request=job_request)

    request = rf.get("/")
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


def test_jobdetail_with_partial_identifier_failure(rf, mocker):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, identifier="123abc")
    JobFactory(job_request=job_request, identifier="123def")

    request = rf.get("/")
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


def test_jobdetail_with_partial_identifier_success(rf):
    job = JobFactory()

    request = rf.get("/")
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


def test_jobdetail_with_unknown_job(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        JobDetail.as_view()(
            request,
            org_slug=job_request.workspace.project.org.slug,
            project_slug=job_request.workspace.project.slug,
            workspace_slug=job_request.workspace.name,
            pk=job_request.pk,
            identifier="test",
        )


def test_jobdetail_without_permission(rf):
    job = JobFactory()

    request = rf.get("/")
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


def test_jobdetailredirect_success(rf):
    job = JobFactory()

    request = rf.get("/")

    response = JobDetailRedirect.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()


def test_jobdetailredirect_with_unknown_job(rf):
    request = rf.get("/")

    with pytest.raises(Http404):
        JobDetailRedirect.as_view()(request, identifier="test")
