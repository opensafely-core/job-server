import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver import honeycomb
from jobserver.authorization import CoreDeveloper, permissions
from jobserver.models import JobRequest
from jobserver.views.jobs import JobCancel, JobDetail, JobDetailRedirect

from ....factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    UserFactory,
)


def test_jobcancel_already_cancelled(rf, user, project_membership, role_factory):
    job_request = JobRequestFactory(cancelled_actions=["another-action", "test"])
    job = JobFactory(job_request=job_request, action="test")

    project_membership(
        project=job_request.workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.job_cancel)],
    )

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action", "test"]


def test_jobcancel_already_completed(rf, user, project_membership, role_factory):
    job_request = JobRequestFactory(cancelled_actions=["another-action"])
    job = JobFactory(job_request=job_request, action="test", status="succeeded")

    project_membership(
        project=job_request.workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.job_cancel)],
    )

    request = rf.post("/")
    request.user = user

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["another-action"]


def test_jobcancel_success(rf, project_membership, role_factory):
    job_request = JobRequestFactory(cancelled_actions=[])
    job = JobFactory(job_request=job_request, action="test")
    user = UserFactory()

    project_membership(
        project=job_request.workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.job_cancel)],
    )

    request = rf.post("/")
    request.user = user

    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == 'Your request to cancel "test" was successful'


def test_jobcancel_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(cancelled_actions=[], created_by=user)
    job = JobFactory(job_request=job_request, action="test")

    request = rf.post("/")
    request.user = user

    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = JobCancel.as_view()(request, identifier=job.identifier)

    assert response.status_code == 302
    assert response.url == job.get_absolute_url()

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["test"]

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == 'Your request to cancel "test" was successful'


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
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content
    assert "Honeycomb" not in response.rendered_content


def test_jobdetail_with_permission(rf, project_membership, role_factory):
    job = JobFactory()
    user = UserFactory()

    project_membership(
        project=job.job_request.workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.job_cancel)],
    )

    request = rf.get("/")
    request.user = user

    response = JobDetail.as_view()(
        request,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content
    assert "Honeycomb" not in response.rendered_content


def test_jobdetail_with_core_developer(rf, time_machine):
    time_machine.move_to("2022-06-16 12:00", tick=False)

    job_request = JobRequestFactory()
    job = JobFactory(
        job_request=job_request, status="succeeded", action="my_sample_action"
    )
    # it's important that the user is associated with the CoreDeveloper role, rather
    # than with a permission that's associated with the CoreDeveloper role
    user = UserFactory(roles=[CoreDeveloper])

    request = rf.get("/")
    request.user = user

    response = JobDetail.as_view()(
        request,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content
    assert "Honeycomb" in response.rendered_content
    assert "trace_end_ts=1655380800" in response.rendered_content
    assert "Previous runs" in response.rendered_content
    assert (
        "%22action%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22my_sample_action%22"
        in response.rendered_content
    )

    # job_requests have prefretch restrictions on them
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()
    url = honeycomb.jobrequest_link(prefetched_job_request)
    assert url in response.rendered_content
    assert job_request.identifier in response.rendered_content


def test_jobdetail_with_core_developer_with_completed_at(rf, time_machine):
    time_machine.move_to("2022-06-15 13:00", tick=False)

    job_request = JobRequestFactory()
    job = JobFactory(
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )

    # it's important that the user is associated with the CoreDeveloper role, rather
    # than with a permission that's associated with the CoreDeveloper role
    user = UserFactory(roles=[CoreDeveloper])

    request = rf.get("/")
    request.user = user

    response = JobDetail.as_view()(
        request,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" not in response.rendered_content
    assert "Honeycomb" in response.rendered_content
    assert "Job Trace" in response.rendered_content
    assert "trace_end_ts=1655298060" in response.rendered_content
    # job_requests have prefretch restrictions on them
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()
    url = honeycomb.jobrequest_link(prefetched_job_request)
    assert url in response.rendered_content
    assert job_request.identifier in response.rendered_content


def test_jobdetail_with_job_creator(rf):
    user = UserFactory()
    job_request = JobRequestFactory(created_by=user)
    job = JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = user

    response = JobDetail.as_view()(
        request,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert "Cancel" in response.rendered_content


def test_jobdetail_with_nonzero_exit_code(rf):
    backend = BackendFactory(slug="tpp", parent_directory="/var/test")
    job_request = JobRequestFactory(backend=backend)
    job = JobFactory(
        job_request=job_request, action="my_action", status_code="nonzero_exit"
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = JobDetail.as_view()(
        request,
        project_slug=job.job_request.workspace.project.slug,
        workspace_slug=job.job_request.workspace.name,
        pk=job.job_request.pk,
        identifier=job.identifier,
    )

    assert response.status_code == 200
    assert (
        response.context_data["log_path"]
        == f"/var/test/{job_request.workspace.name}/metadata/my_action.log"
    )
    assert (
        response.context_data["log_path_url"]
        == f"{job.job_request.workspace.get_files_url()}metadata/my_action.log"
    )


def test_jobdetail_with_partial_identifier_failure(rf):
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, identifier="123abc")
    JobFactory(job_request=job_request, identifier="123def")

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        JobDetail.as_view()(
            request,
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
