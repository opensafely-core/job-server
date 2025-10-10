from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from jobserver.models import Job, JobRequest
from jobserver.models.job_request import JobRequestStatus
from tests.factories import (
    JobFactory,
    JobRequestFactory,
)
from tests.utils import minutes_ago, seconds_ago


def check_job_request_status(rap_id, expected_status):
    job_request: JobRequest = JobRequest.objects.get(identifier=rap_id)
    assert JobRequestStatus(job_request.jobs_status) == expected_status


@pytest.fixture
def now():
    yield timezone.now()


def rap_status_response_factory(jobs, unrecognised_rap_ids, now):
    jobs_response = []
    for job in jobs:
        jobs_response.append(
            {
                "identifier": job.get("identifier", "identifier-0"),
                "rap_id": job.get("rap_id", "rap-identifier-0"),
                "action": job.get("action", "test-action1"),
                "backend": job.get("backend", "test"),
                "run_command": job.get("run_command", "do-research"),
                "requires_db": job.get("requires_db", "false"),
                "status": job.get("status", "succeeded"),
                "status_code": "",
                "status_message": "",
                "created_at": job.get("created_at", minutes_ago(now, 2)),
                "started_at": job.get("started_at", minutes_ago(now, 1)),
                "updated_at": now,
                "completed_at": job.get("completed_at", seconds_ago(now, 30)),
                "metrics": {"cpu_peak": 99},
            }
        )
    return {
        "jobs": jobs_response,
        "unrecognised_rap_ids": unrecognised_rap_ids,
    }


@patch("jobserver.rap_api.status")
def test_update_job_simple(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    job_request = JobRequestFactory()

    assert Job.objects.count() == 0

    job1 = JobFactory.create(
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    assert Job.objects.count() == 1

    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": job1.identifier,
                "rap_id": job_request.identifier,
            }
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    with django_assert_num_queries(5):
        call_command("rap_status", job_request.identifier)

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 1

    # check our jobs look as expected
    updated_job1 = jobs[0]

    assert updated_job1.identifier == job1.identifier
    assert updated_job1.started_at == minutes_ago(now, 1)
    assert updated_job1.updated_at == now
    assert updated_job1.completed_at == seconds_ago(now, 30)
    assert updated_job1.metrics == {"cpu_peak": 99}
    assert (
        log_output.entries[0]["event"]
        == f"RAP: {job_request.identifier} Job: {job1.identifier} Status: succeeded"
    )
    assert log_output.entries[1]["event"] == f"{job1.identifier} newly completed"

    assert log_output.entries[-1]["event"] == "Created, updated or deleted Jobs"
    assert log_output.entries[-1]["updated_job_ids"] == str(job1.id)
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)


@patch("jobserver.rap_api.status")
def test_command_unrecognised_controller(mock_rap_api_status, log_output, now):
    job_request = JobRequestFactory()

    test_response_json = rap_status_response_factory([], [job_request.identifier], now)

    mock_rap_api_status.return_value = test_response_json

    call_command("rap_status", job_request.identifier)

    assert log_output.entries[0]["event"] == "Created, updated or deleted Jobs"
    assert log_output.entries[0]["updated_job_ids"] == ""
    assert log_output.entries[0]["created_job_ids"] == ""
    assert log_output.entries[0]["deleted_job_identifiers"] == ""
    assert (
        log_output.entries[1]["event"]
        == f"Unrecognised RAP ids: {job_request.identifier}"
    )


@patch("jobserver.rap_api.status")
def test_command_unrecognised_jobserver(mock_rap_api_status, log_output, now):
    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": "job1",
                "rap_id": "job_request1",
                "status": "succeeded",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30),
            },
        ],
        [],
        now,
    )

    mock_rap_api_status.return_value = test_response_json

    call_command("rap_status", "job1")

    assert (
        log_output.entries[0]["event"] == "Job-server does not recognise RAP id: job1"
    )


@patch("jobserver.rap_api.status")
def test_command_error(mock_rap_api_status, log_output):
    mock_rap_api_status.side_effect = Exception("something went wrong")

    call_command("rap_status", "abcdefgi12345678")

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])
