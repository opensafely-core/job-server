"""
These tests use responses to patch the requests module where it is used to make calls
to the RAP API. This allows us to test the interface between the rap_api module
and other parts of the system.
"""

from datetime import UTC, datetime

import pytest
import responses
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.urls import reverse

from jobserver.actions.rap import rap_status_update
from jobserver.authorization.permissions import Permission
from jobserver.models import Job, JobRequest, JobRequestStatus
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    WorkspaceFactory,
    rap_status_response_factory,
)
from tests.fakes import FakeGitHubAPI


@pytest.fixture
def setup_backend_workspace_user(mocker, project_membership, role_factory, user):
    backend = BackendFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)
    project_membership(
        project=workspace.project,
        user=user,
        roles=[role_factory(permission=Permission.JOB_RUN)],
    )

    dummy_yaml = """
    version: 4
    actions:
      action1:
        run: test:latest
        outputs:
          moderately_sensitive:
            dataset: path/to/output.csv
    """
    mocker.patch(
        "jobserver.views.job_requests.JobRequestCreate.get_github_api", FakeGitHubAPI
    )
    mocker.patch(
        "jobserver.views.job_requests.get_project",
        autospec=True,
        return_value=dummy_yaml,
    )
    mocker.patch(
        "jobserver.views.job_requests.get_codelists_status",
        autospec=True,
        return_value="ok",
    )
    yield backend, workspace, user


@responses.activate
def test_jobrequestcreate_post_success(client, setup_backend_workspace_user):
    """
    Tests the view that creates a JobRequest and calls the RAP API create endpoint
    """
    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/create/",
        status=201,
        json={"result": "Success", "details": "jobs created", "count": 1},
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    backend, workspace, user = setup_backend_workspace_user

    client.force_login(user)
    url = reverse("job-request-create", args=(workspace.project.slug, workspace.name))

    response = client.post(
        url,
        {
            "backend": backend.slug,
            "requested_actions": ["action1"],
            "callback_url": "test",
        },
    )
    assert response.status_code == 302

    job_request = JobRequest.objects.first()
    assert job_request.jobs_status == JobRequestStatus.PENDING


@responses.activate
def test_jobrequestcreate_post_nothing_to_do(client, setup_backend_workspace_user):
    """
    Tests the view that creates a JobRequest and calls the RAP API create endpoint
    """
    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/create/",
        status=200,
        json={
            "result": "Nothing to do",
            "details": "All actions have already completed successfully",
            "count": 0,
        },
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    backend, workspace, user = setup_backend_workspace_user

    client.force_login(user)
    url = reverse("job-request-create", args=(workspace.project.slug, workspace.name))

    response = client.post(
        url,
        {
            "backend": backend.slug,
            "requested_actions": ["action1"],
            "callback_url": "test",
        },
    )
    assert response.status_code == 302
    job_request = JobRequest.objects.first()
    assert job_request.jobs_status == JobRequestStatus.NOTHING_TO_DO
    assert (
        job_request.status_message == "All actions have already completed successfully"
    )


@responses.activate
def test_jobrequestcreate_post_unexpected_error(client, setup_backend_workspace_user):
    """
    Tests the view that creates a JobRequest and calls the RAP API create endpoint
    """
    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/create/",
        status=500,
        body="",
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    backend, workspace, user = setup_backend_workspace_user

    client.force_login(user)
    url = reverse("job-request-create", args=(workspace.project.slug, workspace.name))

    response = client.post(
        url,
        {
            "backend": backend.slug,
            "requested_actions": ["action1"],
            "callback_url": "test",
        },
    )
    assert response.status_code == 302
    job_request = JobRequest.objects.first()
    assert job_request.jobs_status == JobRequestStatus.UNKNOWN_ERROR_CREATING_JOBS


@responses.activate
def test_jobrequestcancel_post_success(client, setup_backend_workspace_user):
    """
    Tests the view that cancels a JobRequest and calls the RAP API cancel endpoint
    """
    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/cancel/",
        status=200,
        json={"result": "Success", "details": "1 action cancelled", "count": 1},
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    backend, workspace, user = setup_backend_workspace_user
    job_request = JobRequestFactory(
        backend=backend,
        workspace=workspace,
        requested_actions=["action1"],
        created_by=user,
    )
    JobFactory(action="action1", status="pending", job_request=job_request)

    client.force_login(user)
    url = reverse(
        "job-request-cancel",
        args=(workspace.project.slug, workspace.name, job_request.id),
    )

    response = client.post(url, follow=True)
    assert "The requested actions have been cancelled" in response.rendered_content

    job_request.refresh_from_db()
    assert job_request.cancelled_actions == ["action1"]


@responses.activate
def test_rap_status_update(setup_backend_workspace_user):
    """
    Tests the rap_status_update command that calls the RAP API status endpoint for job updates
    """

    backend, workspace, _ = setup_backend_workspace_user
    job_request = JobRequestFactory(
        backend=backend, workspace=workspace, requested_actions=["action1"]
    )
    assert Job.objects.count() == 0

    response_json = rap_status_response_factory(
        [
            {
                "identifier": "new-job-identifier",
                "rap_id": job_request.identifier,
                "status": "running",
            }
        ],
        [],
        datetime(2025, 3, 1, 10, 0, tzinfo=UTC),
    )

    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/status/",
        status=200,
        json=response_json,
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    rap_status_update([job_request.identifier])

    assert Job.objects.count() == 1
    assert Job.objects.first().identifier == "new-job-identifier"
    job_request.refresh_from_db()
    assert job_request.jobs_status == JobRequestStatus.RUNNING


@responses.activate
def test_rap_status_update_notifications_on(setup_backend_workspace_user):
    """
    Tests the rap_status_update command that calls the RAP API status endpoint for job updates
    """

    backend, workspace, _ = setup_backend_workspace_user
    job_request = JobRequestFactory(
        backend=backend,
        workspace=workspace,
        requested_actions=["action1"],
        will_notify=True,
    )
    running_job = JobFactory(job_request=job_request, status="running")
    completed_job = JobFactory(job_request=job_request, status="succeeded")
    assert Job.objects.count() == 2

    response_json = rap_status_response_factory(
        [
            # new job, not newly completed
            {
                "identifier": "new-running-job",
                "rap_id": job_request.identifier,
                "status": "running",
            },
            # new job, newly completed, should notify
            {
                "identifier": "new-completed-job",
                "rap_id": job_request.identifier,
                "status": "succeeded",
            },
            # existing job already completed
            {
                "identifier": completed_job.identifier,
                "rap_id": job_request.identifier,
                "status": "succeeded",
            },
            # existing job newly completed, should notify
            {
                "identifier": running_job.identifier,
                "rap_id": job_request.identifier,
                "status": "succeeded",
            },
        ],
        [],
        datetime(2025, 3, 1, 10, 0, tzinfo=UTC),
    )

    responses.post(
        url=f"{settings.RAP_API_BASE_URL}rap/status/",
        status=200,
        json=response_json,
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    rap_status_update([job_request.identifier])

    assert Job.objects.count() == 4

    job_request.refresh_from_db()
    assert job_request.jobs_status == JobRequestStatus.RUNNING

    # One mail sent for each completed job
    assert len(mail.outbox) == 2


@responses.activate
def test_backend_status():
    """
    Tests the rap_update_backend_status management command that calls the RAP API backend status endpoint
    """
    backend1 = BackendFactory()
    backend2 = BackendFactory()
    responses.get(
        url=f"{settings.RAP_API_BASE_URL}backend/status/",
        status=200,
        json={
            "backends": [
                {
                    "slug": backend1.slug,
                    "last_seen": "2025-10-01T10:30:55.123456Z",
                    "paused": {
                        "status": "off",
                        "since": "2025-01-01T10:30:55.123456Z",
                    },
                    "db_maintenance": {
                        "status": "off",
                        "since": None,
                        "type": None,
                    },
                },
                {
                    "slug": backend2.slug,
                    "last_seen": "2025-10-10T12:30:55.123456Z",
                    "paused": {
                        "status": "off",
                        "since": None,
                    },
                    "db_maintenance": {
                        "status": "on",
                        "since": "2025-10-09T11:30:55.123456Z",
                        "type": None,
                    },
                },
            ]
        },
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    call_command("rap_update_backend_status")
    backend1.refresh_from_db()
    backend2.refresh_from_db()

    assert not backend1.is_in_maintenance_mode
    assert backend1.last_seen_maintenance_mode is None
    assert backend1.last_seen_at == datetime.fromisoformat(
        "2025-10-01T10:30:55.123456Z"
    )
    assert backend2.is_in_maintenance_mode
    assert backend2.last_seen_maintenance_mode == datetime.fromisoformat(
        "2025-10-09T11:30:55.123456Z"
    )
    assert backend2.last_seen_at == datetime.fromisoformat(
        "2025-10-10T12:30:55.123456Z"
    )
