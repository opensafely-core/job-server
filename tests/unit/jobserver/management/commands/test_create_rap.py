from unittest.mock import patch

import pytest
from django.core.management import call_command

from jobserver.models import JobRequest, JobRequestStatus
from jobserver.rap_api import RapAPIRequestError, RapAPIResponseError
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
    ):
        yield


@patch("jobserver.rap_api.create")
def test_create_command(mock_rap_api_create, log_output, setup):
    assert JobRequest.objects.count() == 0
    test_response_json = {
        "result": "Success",
        "count": 1,
    }
    mock_rap_api_create.return_value = test_response_json

    call_command("create_rap", *_FAKE_ARGS)

    assert log_output.entries[0] == {
        "event": test_response_json,
        "log_level": "info",
    }

    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert job_request.requested_actions == ["action1", "action2"]
    assert job_request.sha == "abc123"  # as returned by FakeGitHubApi
    assert JobRequestStatus(job_request.status) == JobRequestStatus.PENDING


@patch("jobserver.rap_api.create")
def test_create_command_with_commit(mock_rap_api_create, log_output, setup):
    assert JobRequest.objects.count() == 0
    test_response_json = {
        "result": "Success",
        "count": 1,
    }
    mock_rap_api_create.return_value = test_response_json

    call_command("create_rap", *_FAKE_ARGS, "--commit", "123456")

    assert log_output.entries[0] == {
        "event": test_response_json,
        "log_level": "info",
    }

    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert job_request.sha == "123456"
    assert JobRequestStatus(job_request.status) == JobRequestStatus.PENDING


@patch("jobserver.rap_api.create")
def test_create_command_nothing_to_do(mock_rap_api_create, log_output, setup):
    assert JobRequest.objects.count() == 0
    test_response_json = {
        "result": "Nothing to do",
        "details": "Already done",
        "count": 0,
    }
    mock_rap_api_create.return_value = test_response_json

    call_command("create_rap", *_FAKE_ARGS)

    assert log_output.entries[0] == {
        "event": test_response_json,
        "log_level": "info",
    }

    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert JobRequestStatus(job_request.status) == JobRequestStatus.NOTHING_TO_DO
    assert job_request.status_message == "Already done"


@patch("jobserver.rap_api.create")
def test_create_command_failed_with_response(mock_rap_api_create, log_output, setup):
    """Test that an error response from the RAP API is marked as failed"""
    mock_rap_api_create.side_effect = RapAPIResponseError(
        "something went wrong", body={"error": "error", "details": "err"}
    )

    call_command("create_rap", *_FAKE_ARGS)

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])

    # A JobRequest is still created, but immediately marked failed
    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert JobRequestStatus(job_request.status) == JobRequestStatus.FAILED
    assert job_request.status_message == "err"


@patch("jobserver.rap_api.create")
def test_create_command_failed_to_request(mock_rap_api_create, log_output, setup):
    """Test that a failure to get a response from the RAP API is marked as unknown"""
    mock_rap_api_create.side_effect = RapAPIRequestError("something went wrong")

    call_command("create_rap", *_FAKE_ARGS)

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])

    # A JobRequest is still created, but immediately marked failed
    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert JobRequestStatus(job_request.status) == JobRequestStatus.UNKNOWN
    assert job_request.status_message is None


@patch("jobserver.rap_api.create")
def test_command_error(mock_rap_api_create, log_output, setup):
    """Test that an unhandled error is marked as failed"""
    mock_rap_api_create.side_effect = Exception("something went wrong")

    call_command("create_rap", *_FAKE_ARGS)

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])

    # A JobRequest is still created, and marked as failed
    assert JobRequest.objects.count() == 1
    job_request = JobRequest.objects.first()
    assert JobRequestStatus(job_request.status) == JobRequestStatus.FAILED
    assert job_request.status_message == "Unknown error creating jobs"
