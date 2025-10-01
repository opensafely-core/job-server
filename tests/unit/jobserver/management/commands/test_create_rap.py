from unittest.mock import patch

import pytest
from django.core.management import call_command

from jobserver.models import JobRequest
from tests.factories import (
    BackendFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI


_FAKE_ARGS = ("test-workspace", "test_user", "test-backend", "-a", "action1", "action2")


@pytest.fixture()
def setup():
    BackendFactory(slug="test-backend")
    UserFactory(username="test_user")
    project = ProjectFactory()
    WorkspaceFactory(name="test-workspace", branch="main", project=project)

    dummy_yaml = """
    version: 4
    actions:
        action1:
            run: test:latest
                outputs:
                    moderately_sensitive:
                        dataset: path/to/output.csv
        action2:
            run: test:latest
                outputs:
                    moderately_sensitive:
                        dataset: path/to/output1.csv
    """

    with (
        patch(
            "jobserver.management.commands.create_rap._get_github_api", FakeGitHubAPI
        ),
        patch(
            "jobserver.management.commands.create_rap.get_codelists_status",
            autospec=True,
            return_value="ok",
        ),
        patch(
            "jobserver.management.commands.create_rap.get_project",
            autospec=True,
            return_value=dummy_yaml,
        ),
        patch(
            "jobserver.models.job_request.JobRequest.request_rap_creation",
            autospec=True,
        ),
    ):
        yield


def test_create_command(setup):
    assert JobRequest.objects.count() == 0

    call_command("create_rap", *_FAKE_ARGS)

    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert job_request.requested_actions == ["action1", "action2"]
    assert job_request.sha == "abc123"  # as returned by FakeGitHubApi


def test_create_command_with_commit(setup):
    assert JobRequest.objects.count() == 0

    call_command("create_rap", *_FAKE_ARGS, "--commit", "123456")

    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert job_request.sha == "123456"
