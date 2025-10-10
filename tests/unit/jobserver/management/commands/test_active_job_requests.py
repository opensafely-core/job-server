from unittest.mock import patch

from django.core.management import call_command

from jobserver.models import JobRequestStatus
from tests.factories import BackendFactory, JobRequestFactory


def test_call_rap_status_command(log_output):
    call_command("active_job_requests")

    assert log_output.entries[0]["log_level"] == "info"
    assert log_output.entries[0]["event"] == "Active job requests"
    assert log_output.entries[0]["rap_ids"] == []


def test_call_rap_status_command_with_job_requests(log_output):
    backend = BackendFactory()
    backend.slug = "test"
    backend.save()

    jr1 = JobRequestFactory(backend=backend, _status=JobRequestStatus.PENDING)
    jr2 = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    jr3 = JobRequestFactory(backend=backend, _status=JobRequestStatus.UNKNOWN)
    jr4 = JobRequestFactory(
        backend=backend, _status=JobRequestStatus.UNKNOWN_ERROR_CREATING_JOBS
    )
    JobRequestFactory(backend=backend, _status=JobRequestStatus.FAILED)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.SUCCEEDED)

    call_command("active_job_requests")

    assert log_output.entries[0]["log_level"] == "info"
    assert log_output.entries[0]["event"] == "Active job requests"
    assert log_output.entries[0]["rap_ids"] == [
        jr1.identifier,
        jr2.identifier,
        jr3.identifier,
        jr4.identifier,
    ]


@patch(
    "jobserver.management.commands.active_job_requests.get_active_job_request_identifiers",
    autospec=True,
)
def test_command_error(mock_get_active_job_requests, log_output):
    mock_get_active_job_requests.side_effect = Exception("something went wrong")

    call_command("active_job_requests")

    assert log_output.entries[0]["log_level"] == "error"
    assert "something went wrong" in str(log_output.entries[0]["event"])
