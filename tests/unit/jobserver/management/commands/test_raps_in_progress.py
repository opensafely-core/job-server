from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone

from jobserver.models import Job
from tests.factories import (
    JobFactory,
    JobRequestFactory,
)
from tests.utils import minutes_ago, seconds_ago


@patch("jobserver.rap_api.status")
def test_update_jobs_multiple_job_requests(mock_rap_api_status, log_output):
    job_request1 = JobRequestFactory()
    job_request2 = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    job1, job2 = JobFactory.create_batch(
        2,
        job_request=job_request1,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    job3, job4 = JobFactory.create_batch(
        2,
        job_request=job_request2,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    assert Job.objects.count() == 4

    test_response_json = {
        "jobs": [
            {
                "identifier": job1.identifier,
                "rap_id": job_request1.identifier,
                "action": "test-action1",
                "backend": "test",
                "run_command": "do-research",
                "status": "succeeded",
                "status_code": "",
                "status_message": "",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "updated_at": now,
                "completed_at": seconds_ago(now, 30),
                "metrics": {"cpu_peak": 99},
            },
            {
                "identifier": job2.identifier,
                "rap_id": job_request1.identifier,
                "action": "test-action2",
                "backend": "test",
                "run_command": "do-research",
                "status": "running",
                "status_code": "",
                "status_message": "",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "updated_at": now,
                "completed_at": None,
            },
            {
                "identifier": job3.identifier,
                "rap_id": job_request2.identifier,
                "action": "test-action2",
                "backend": "test",
                "run_command": "do-research",
                "status": "running",
                "status_code": "",
                "status_message": "",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "updated_at": now,
                "completed_at": None,
            },
            {
                "identifier": job4.identifier,
                "rap_id": job_request2.identifier,
                "action": "test-action3",
                "backend": "test",
                "run_command": "do-research",
                "status": "pending",
                "status_code": "",
                "status_message": "",
                "created_at": minutes_ago(now, 2),
                "started_at": None,
                "updated_at": now,
                "completed_at": None,
            },
        ],
        "unrecognised_rap_ids": [],
    }
    mock_rap_api_status.return_value = test_response_json

    call_command("raps_in_progress")

    # Check the command worked overall
    assert log_output.entries[-1]["event"] == "Created, updated or deleted Jobs"
    assert (
        log_output.entries[-1]["updated_job_ids"]
        == f"{job1.id},{job2.id},{job3.id},{job4.id}"
    )

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 4

    # Check the details of the jobs
    updated_job1, updated_job2, updated_job3, updated_job4 = jobs

    # job_request1 job succeeded
    assert updated_job1.identifier == job1.identifier
    assert updated_job1.started_at == minutes_ago(now, 1)
    assert updated_job1.updated_at == now
    assert updated_job1.completed_at == seconds_ago(now, 30)
    assert updated_job1.metrics == {"cpu_peak": 99}
    assert (
        log_output.entries[0]["event"]
        == f"RAP: {job_request1.identifier} Job: {job1.identifier} Status: succeeded"
    )
    assert log_output.entries[1]["event"] == f"{job1.identifier} newly completed"

    # job_request1 job running
    assert updated_job2.identifier == job2.identifier
    assert updated_job2.started_at == minutes_ago(now, 1)
    assert updated_job2.updated_at == now
    assert updated_job2.completed_at is None
    assert (
        log_output.entries[2]["event"]
        == f"RAP: {job_request1.identifier} Job: {job2.identifier} Status: running"
    )

    # job_request2 job running
    assert updated_job3.identifier == job3.identifier
    assert updated_job3.started_at == minutes_ago(now, 1)
    assert updated_job3.updated_at == now
    assert updated_job3.completed_at is None
    assert (
        log_output.entries[3]["event"]
        == f"RAP: {job_request2.identifier} Job: {job3.identifier} Status: running"
    )

    # job_request2 job pending
    assert updated_job4.identifier == job4.identifier
    assert updated_job4.started_at is None
    assert updated_job4.updated_at == now
    assert updated_job4.completed_at is None
    assert (
        log_output.entries[4]["event"]
        == f"RAP: {job_request2.identifier} Job: {job4.identifier} Status: pending"
    )


def test_update_jobs_nothing_active(log_output):
    call_command("raps_in_progress")

    # Check the command worked overall
    assert log_output.entries[-1]["event"] == "No active RAPs"
