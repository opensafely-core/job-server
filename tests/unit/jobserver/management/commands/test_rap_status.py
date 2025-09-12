from copy import deepcopy
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
    assert JobRequestStatus(job_request.status) == expected_status
    assert JobRequestStatus(job_request.jobs_status) == expected_status


@patch("jobserver.rap_api.status")
def test_update_job_simple(mock_rap_api_status, log_output):
    job_request = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    job1 = JobFactory.create(
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    assert Job.objects.count() == 1

    test_response_json = {
        "jobs": [
            {
                "identifier": job1.identifier,
                "rap_id": job_request.identifier,
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
        ],
        "unrecognised_rap_ids": [],
    }
    mock_rap_api_status.return_value = test_response_json

    call_command("rap_status", job_request.identifier)

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 1

    # check our jobs look as expected
    updated_job1 = jobs[0]

    # succeeded
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


@pytest.mark.parametrize("pre_existing", [True, False])
@patch("jobserver.rap_api.status")
def test_update_job_multiple(mock_rap_api_status, log_output, pre_existing):
    job_request = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    if pre_existing:
        # 3 pending jobs already exist
        job1, job2, job3 = JobFactory.create_batch(
            3,
            job_request=job_request,
            started_at=None,
            status="pending",
            completed_at=None,
        )
        job1.identifier = "job1"
        job1.save()

        job2.identifier = "job2"
        job2.save()

        job3.identifier = "job3"
        job3.save()

        assert Job.objects.count() == 3

    test_response_json = {
        "jobs": [
            {
                "identifier": "job1",
                "rap_id": job_request.identifier,
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
                "identifier": "job2",
                "rap_id": job_request.identifier,
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
                "identifier": "job3",
                "rap_id": job_request.identifier,
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

    call_command("rap_status", job_request.identifier)

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 3

    # check our jobs look as expected
    job1, job2, job3 = jobs

    # succeeded
    assert job1.identifier == "job1"
    assert job1.started_at == minutes_ago(now, 1)
    assert job1.updated_at == now
    assert job1.completed_at == seconds_ago(now, 30)
    assert job1.metrics == {"cpu_peak": 99}
    assert (
        log_output.entries[0]["event"]
        == f"RAP: {job_request.identifier} Job: job1 Status: succeeded"
    )
    assert log_output.entries[1]["event"] == f"{job1.identifier} newly completed"

    # running
    assert job2.identifier == "job2"
    assert job2.started_at == minutes_ago(now, 1)
    assert job2.updated_at == now
    assert job2.completed_at is None
    assert (
        log_output.entries[2]["event"]
        == f"RAP: {job_request.identifier} Job: job2 Status: running"
    )

    # pending
    assert job3.identifier == "job3"
    assert job3.started_at is None
    assert job3.updated_at == now
    assert job3.completed_at is None
    assert (
        log_output.entries[3]["event"]
        == f"RAP: {job_request.identifier} Job: job3 Status: pending"
    )

    assert log_output.entries[4]["event"] == "Created, updated or deleted Jobs"
    if pre_existing:
        assert (
            log_output.entries[4]["updated_job_ids"] == f"{job1.id},{job2.id},{job3.id}"
        )
    else:
        assert (
            log_output.entries[4]["created_job_ids"] == f"{job1.id},{job2.id},{job3.id}"
        )

    check_job_request_status(job_request.identifier, JobRequestStatus.RUNNING)


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

    call_command("rap_status", [job_request1.identifier, job_request2.identifier])

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

    check_job_request_status(job_request1.identifier, JobRequestStatus.RUNNING)
    check_job_request_status(job_request2.identifier, JobRequestStatus.RUNNING)


@patch("jobserver.rap_api.status")
def test_delete_jobs(mock_rap_api_status, log_output):
    job_request = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    jobs = JobFactory.create_batch(
        2,
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )

    # rap/status only returns one job of the two created
    test_response_json = {
        "jobs": [
            {
                "identifier": jobs[0].identifier,
                "rap_id": job_request.identifier,
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
            }
        ],
        "unrecognised_rap_ids": [],
    }

    identifier_to_delete = jobs[1].identifier

    assert Job.objects.count() == 2

    mock_rap_api_status.return_value = test_response_json

    call_command("rap_status", job_request.identifier)

    # The second job should have been deleted
    jobs = Job.objects.all()
    assert len(jobs) == 1

    assert log_output.entries[-1]["event"] == "Created, updated or deleted Jobs"
    assert log_output.entries[-1]["updated_job_ids"] == str(jobs[0].id)
    assert log_output.entries[-1]["deleted_job_identifiers"] == identifier_to_delete

    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)


@pytest.mark.slow_test
@patch("jobserver.rap_api.status")
def test_update_lots_of_jobs(mock_rap_api_status, log_output):
    job_request = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    jobs = JobFactory.create_batch(
        5000,
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )

    test_response_json = {
        "jobs": [],
        "unrecognised_rap_ids": [],
    }

    for job in jobs:
        test_response_json["jobs"].append(
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
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
            }
        )

    assert Job.objects.count() == 5000

    mock_rap_api_status.return_value = test_response_json

    call_command("rap_status", job_request.identifier)

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 5000

    assert log_output.entries[-1]["event"] == "Created, updated or deleted Jobs"

    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)


@patch("jobserver.rap_api.status")
def test_flip_flop_updates(mock_rap_api_status, log_output):
    job_request = JobRequestFactory()

    now = timezone.now()

    job = JobFactory.create(
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    test_job_id = job.id

    test_response_json_stale = {
        "jobs": [
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
                "action": "test-action1",
                "backend": "test",
                "run_command": "do-research",
                "status": "running",
                "status_code": "",
                "status_message": "",
                "created_at": minutes_ago(now, 1),
                "started_at": now,
                "updated_at": now,
                "completed_at": None,
                "metrics": {"cpu_peak": 99},
            }
        ],
        "unrecognised_rap_ids": [],
    }
    test_response_json_fresh = {
        "jobs": [
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
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
            }
        ],
        "unrecognised_rap_ids": [],
    }

    # The rap_status command will modify the returned dict in place,
    # so use a deepcopy so that our test will work as expected!
    mock_rap_api_status.return_value = deepcopy(test_response_json_stale)
    call_command("rap_status", job_request.identifier)
    job = Job.objects.get(id=test_job_id)
    assert job.status == "running"
    check_job_request_status(job_request.identifier, JobRequestStatus.RUNNING)

    mock_rap_api_status.return_value = deepcopy(test_response_json_fresh)
    call_command("rap_status", job_request.identifier)
    job = Job.objects.get(id=test_job_id)
    assert job.status == "succeeded"
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)

    mock_rap_api_status.return_value = deepcopy(test_response_json_stale)
    call_command("rap_status", job_request.identifier)
    job = Job.objects.get(id=test_job_id)
    assert job.status == "running"
    # Once a JobRequest hits a completed state, it stays there
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)

    mock_rap_api_status.return_value = deepcopy(test_response_json_fresh)
    call_command("rap_status", job_request.identifier)
    job = Job.objects.get(id=test_job_id)
    assert job.status == "succeeded"
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)


@patch("jobserver.rap_api.status")
def test_command_unrecognised_controller(mock_rap_api_status, log_output):
    job_request = JobRequestFactory()

    test_response_json = {"jobs": [], "unrecognised_rap_ids": [job_request.identifier]}

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
def test_command_unrecognised_jobserver(mock_rap_api_status, log_output):
    now = timezone.now()

    test_response_json = {
        "jobs": [
            {
                "identifier": "job1",
                "rap_id": "job_request1",
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
        ],
        "unrecognised_rap_ids": [],
    }

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
