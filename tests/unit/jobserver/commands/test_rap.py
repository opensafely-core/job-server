from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from jobserver.commands import rap
from jobserver.models import Job, JobRequest, JobRequestStatus
from tests.factories import BackendFactory, JobFactory, JobRequestFactory
from tests.utils import minutes_ago, seconds_ago


@pytest.fixture
def now():
    yield timezone.now()


def test_get_active_job_request_ids():
    backend = BackendFactory()
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobFactory(job_request=job_request, status="running")
    active_job_request_ids = rap.get_active_job_request_ids()
    assert active_job_request_ids == [job_request.identifier]


def test_get_active_job_request_ids_stale_status():
    backend = BackendFactory()
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobFactory(job_request=job_request, status="completed")
    active_job_request_ids = rap.get_active_job_request_ids()
    assert active_job_request_ids == []


def test_get_active_job_request_ids_no_jobs():
    backend = BackendFactory()
    # none of these are considered active by the current code
    JobRequestFactory(backend=backend, _status=JobRequestStatus.PENDING)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.UNKNOWN)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.FAILED)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.SUCCEEDED)
    JobRequestFactory(backend=BackendFactory(), _status=JobRequestStatus.RUNNING)
    active_job_request_ids = rap.get_active_job_request_ids()
    assert active_job_request_ids == []


def test_get_active_job_request_ids_historical():
    backend = BackendFactory()
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    two_years_ago = timezone.now() - timedelta(weeks=104)
    JobFactory(job_request=job_request, status="unknown", created_at=two_years_ago)
    active_job_request_ids = rap.get_active_job_request_ids()
    assert active_job_request_ids == []


def check_job_request_status(rap_id, expected_status):
    job_request: JobRequest = JobRequest.objects.get(identifier=rap_id)
    assert JobRequestStatus(job_request.jobs_status) == expected_status


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


# TODO: move other management command tests to here
@patch("jobserver.rap_api.status")
def test_rap_status_update_simple(
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

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 3) Retrieve statuses for existing jobs
    # 4-7) update_or_create on the job returned in the response
    with django_assert_num_queries(7):
        rap.rap_status_update([job_request.identifier])

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
    assert log_output.entries[-1]["event"] == "Created or updated Jobs"
    assert log_output.entries[-1]["updated_job_ids"] == [job1.id]
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)


@patch("jobserver.rap_api.status")
def test_rap_status_update_create_job(
    mock_rap_api_status, django_assert_num_queries, now
):
    job_request = JobRequestFactory()

    assert Job.objects.count() == 0

    test_response_json = rap_status_response_factory(
        [
            {"rap_id": job_request.identifier, "identifier": "new-job-identifier"},
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 3) Retrieve statuses for existing jobs
    # 4-9) update_or_create on the job returned in the response (create requires 2 additional queries to update)
    with django_assert_num_queries(9):
        rap.rap_status_update([job_request.identifier])

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 1

    # check our jobs look as expected
    updated_job = jobs[0]
    assert updated_job.identifier == "new-job-identifier"


@patch("jobserver.rap_api.status")
def test_rap_status_update_multiple_raps(
    mock_rap_api_status, django_assert_num_queries, now
):
    job_request1 = JobRequestFactory()
    job_request2 = JobRequestFactory()

    assert Job.objects.count() == 0

    job1 = JobFactory.create(
        job_request=job_request1,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    job2 = JobFactory.create(
        job_request=job_request2,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    assert Job.objects.count() == 2

    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": job1.identifier,
                "rap_id": job_request1.identifier,
            },
            {
                "identifier": job2.identifier,
                "rap_id": job_request2.identifier,
            },
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 3) Retrieve statuses for existing jobs
    # 4-7, 8-11) update_or_create on each job returned in the response
    with django_assert_num_queries(11):
        rap.rap_status_update([job_request1.identifier, job_request2.identifier])

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 2

    # check our jobs look as expected
    updated_job1 = jobs[0]
    updated_job2 = jobs[1]
    assert updated_job1.identifier == job1.identifier
    assert updated_job2.identifier == job2.identifier
