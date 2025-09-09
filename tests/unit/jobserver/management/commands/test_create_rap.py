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
    assert JobRequest.objects.first().requested_actions == ["action1", "action2"]
    assert JobRequest.objects.first().sha == "abc123"  # as returned by FakeGitHubApi


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
    assert JobRequest.objects.first().sha == "123456"


@patch("jobserver.rap_api.create")
def test_command_error(mock_rap_api_create, log_output, setup):
    mock_rap_api_create.side_effect = Exception("something went wrong")

    call_command("create_rap", *_FAKE_ARGS)

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])
