"""
These tests use responses to patch the requests module where it is used to make calls
to the RAP API. This allows us to test the interface between the rap_api module
and other parts of the system.
"""

import pytest
import responses
from django.conf import settings
from django.urls import reverse

from jobserver.authorization import permissions
from jobserver.models import JobRequest, JobRequestStatus
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    WorkspaceFactory,
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
        roles=[role_factory(permission=permissions.job_run)],
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
        json={"success": "ok", "details": "1 action cancelled", "count": 1},
        match=[
            responses.matchers.header_matcher({"Authorization": settings.RAP_API_TOKEN})
        ],
    )

    backend, workspace, user = setup_backend_workspace_user
    job_request = JobRequestFactory(
        backend=backend, workspace=workspace, requested_actions=["action1"]
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
