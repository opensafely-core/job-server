from django.urls import reverse
from opentelemetry import trace

from jobserver.authorization import permissions
from jobserver.models import JobRequest
from tests.conftest import get_trace

from ...factories import (
    BackendFactory,
    BackendMembershipFactory,
    WorkspaceFactory,
)
from ...fakes import FakeGitHubAPI


def test_jobrequestcreate_post_telemetry(
    client,
    mocker,
    user,
    project_membership,
    role_factory,
):
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
      twiddle:
        run: test:latest
        outputs:
          moderately_sensitive:
            cohort: path/to/output.csv
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
    mocker.patch(
        "jobserver.models.job_request.rap_api.create",
        autospec=True,
        return_value={"count": 1, "details": "jobs created"},
    )

    client.force_login(user)
    url = reverse("job-request-create", args=(workspace.project.slug, workspace.name))

    # In tests the parent span (set in middleware, by the django instrumentation)
    # is a NonRecordingSpan, so call the endpoint inside another span so
    # so we can assert that the attrtibutes are added during the view
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("mock_django_span"):
        response = client.post(
            url,
            {
                "backend": backend.slug,
                "requested_actions": ["twiddle"],
                "callback_url": "test",
            },
        )
    assert response.status_code == 302

    job_request = JobRequest.objects.first()
    assert job_request.workspace == workspace
    assert job_request.requested_actions == ["twiddle"]

    traced_attributes = {trace.name: trace.attributes for trace in get_trace()}
    assert set(traced_attributes.keys()) == {"mock_django_span", "create_rap"}

    for attributes in traced_attributes.values():
        assert attributes["rap_id"] == job_request.identifier
        assert attributes["requested_actions"] == ("twiddle",)
