import logging
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from jobserver.actions import rap
from jobserver.models import Job, JobRequest, JobRequestStatus
from tests.conftest import get_trace
from tests.factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    WorkspaceFactory,
    rap_status_response_factory,
)
from tests.utils import minutes_ago, seconds_ago


@pytest.fixture
def now():
    yield timezone.now()


@pytest.fixture()
def debug_log_output(log_output):
    # Ensure DEBUG level logs are visible
    logger = logging.getLogger("jobserver.actions.rap")
    old_level = logger.level
    logger.setLevel(logging.DEBUG)
    yield log_output
    logger.setLevel(old_level)


def test_get_active_job_request_ids():
    backend = BackendFactory()
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobFactory(job_request=job_request, status="running")
    active_job_request_ids = rap.get_active_job_request_identifiers()
    assert active_job_request_ids == [job_request.identifier]


def test_get_active_job_request_ids_stale_status():
    backend = BackendFactory()
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobFactory(job_request=job_request, status="succeeded")
    active_job_request_ids = rap.get_active_job_request_identifiers()
    assert active_job_request_ids == []


def test_get_active_job_request_ids_no_jobs():
    backend = BackendFactory()
    # Job requests with active _status are still considered active even if they have no jobs
    jr1 = JobRequestFactory(backend=backend, _status=JobRequestStatus.PENDING)
    jr2 = JobRequestFactory(backend=backend, _status=JobRequestStatus.UNKNOWN)
    jr3 = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.FAILED)
    JobRequestFactory(backend=backend, _status=JobRequestStatus.SUCCEEDED)
    # job-request for alternative backend
    jr4 = JobRequestFactory(backend=BackendFactory(), _status=JobRequestStatus.RUNNING)
    active_job_request_ids = rap.get_active_job_request_identifiers()
    assert active_job_request_ids == [
        jr1.identifier,
        jr2.identifier,
        jr3.identifier,
        jr4.identifier,
    ]


def test_get_active_job_request_ids_historical():
    backend = BackendFactory()
    # active job request (no jobs)
    job_request = JobRequestFactory(backend=backend, _status=JobRequestStatus.RUNNING)

    # old job request (no jobs)
    two_years_ago = timezone.now() - timedelta(weeks=104)
    JobRequestFactory(
        backend=backend, _status=JobRequestStatus.UNKNOWN, created_at=two_years_ago
    )

    # old job request (unknown status jobs)
    old_job_request = JobRequestFactory(
        backend=backend, _status=JobRequestStatus.UNKNOWN, created_at=two_years_ago
    )
    JobFactory(job_request=old_job_request, status="unknown")

    # old job request (active jobs)
    old_job_request_with_active_jobs = JobRequestFactory(
        backend=backend, _status=JobRequestStatus.UNKNOWN, created_at=two_years_ago
    )
    JobFactory(job_request=old_job_request_with_active_jobs, status="pending")

    active_job_request_ids = rap.get_active_job_request_identifiers()
    assert active_job_request_ids == [
        job_request.identifier,
        old_job_request_with_active_jobs.identifier,
    ]


def check_job_request_status(rap_id, expected_status):
    job_request: JobRequest = JobRequest.objects.get(identifier=rap_id)
    assert JobRequestStatus(job_request.jobs_status) == expected_status
    # return the refreshed job request for tests that need to use it
    return job_request


@patch("jobserver.rap_api.status")
def test_rap_status_update_single_job_request(
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
    # 3-6) update_or_create on the job returned in the response
    with django_assert_num_queries(6):
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

    spans = get_trace()
    assert spans[0].attributes["rap_status.updated_job_identifiers"] == job1.identifier
    assert spans[0].attributes["rap_status.affected_job_count"] == 1
    assert spans[0].attributes["rap_status.created_job_count"] == 0
    assert spans[0].attributes["rap_status.updated_job_count"] == 1


@patch("jobserver.rap_api.status")
def test_rap_status_update_single_job_request_create_job(
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
    # 3-8) update_or_create on the job returned in the response (create requires 2 additional queries to update)
    with django_assert_num_queries(8):
        rap.rap_status_update([job_request.identifier])

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 1

    # check our jobs look as expected
    updated_job = jobs[0]
    assert updated_job.identifier == "new-job-identifier"

    spans = get_trace()
    assert (
        spans[0].attributes["rap_status.created_job_identifiers"]
        == updated_job.identifier
    )
    assert spans[0].attributes["rap_status.affected_job_count"] == 1
    assert spans[0].attributes["rap_status.created_job_count"] == 1
    assert spans[0].attributes["rap_status.updated_job_count"] == 0


@patch("jobserver.rap_api.status")
def test_rap_status_update_single_job_for_multiple_job_requests(
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
    # 3-6, 7-10) update_or_create on each job returned in the response
    with django_assert_num_queries(10):
        rap.rap_status_update([job_request1.identifier, job_request2.identifier])

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 2

    # check our jobs look as expected
    updated_job1 = jobs[0]
    updated_job2 = jobs[1]
    assert updated_job1.identifier == job1.identifier
    assert updated_job2.identifier == job2.identifier

    spans = get_trace()
    assert (
        spans[0].attributes["rap_status.updated_job_identifiers"]
        == f"{job1.identifier},{job2.identifier}"
    )
    assert spans[0].attributes["rap_status.affected_job_count"] == 2
    assert spans[0].attributes["rap_status.created_job_count"] == 0
    assert spans[0].attributes["rap_status.updated_job_count"] == 2


@pytest.mark.parametrize(
    # Query counts: 2 initial queries to get all matching job requests, prefetching jobs
    # Then 4 queries per job (3 jobs in test) to update or 6 queries per job to create
    "pre_existing, query_count",
    [(True, 2 + 3 * 4), (False, 2 + 3 * 6)],
)
@patch("jobserver.rap_api.status")
def test_update_job_multiple(
    mock_rap_api_status,
    debug_log_output,
    pre_existing,
    query_count,
    django_assert_num_queries,
    now,
):
    job_request = JobRequestFactory()

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

    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": "job1",
                "rap_id": job_request.identifier,
                "action": "test-action1",
                "status": "succeeded",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30),
            },
            {
                "identifier": "job2",
                "rap_id": job_request.identifier,
                "action": "test-action2",
                "status": "running",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": None,
            },
            {
                "identifier": "job3",
                "rap_id": job_request.identifier,
                "action": "test-action3",
                "status": "pending",
                "created_at": minutes_ago(now, 2),
                "started_at": None,
                "completed_at": None,
            },
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    with django_assert_num_queries(query_count):
        rap.rap_status_update([job_request.identifier])

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 3

    # check our jobs look as expected
    job1, job2, job3 = jobs

    def assert_log(log, expected):
        # remove the timestamp; we expect it to be there, but we
        # don't need to test it
        assert "timestamp" in log, log.items()
        log.pop("timestamp", None)
        # context that we expect to be added to all logs
        expected.update(
            {
                "log_level": "debug",
                "job_request": job_request.id,
                "logger": "jobserver.actions.rap",
            }
        )
        assert log == expected, log

    spans = get_trace()

    # succeeded
    assert job1.identifier == "job1"
    assert job1.started_at == minutes_ago(now, 1)
    assert job1.updated_at == now
    assert job1.completed_at == seconds_ago(now, 30)
    assert job1.metrics == {"cpu_peak": 99}

    assert_log(
        debug_log_output.entries[0],
        {
            "event": "RAP Job Status",
            "level": "debug",
            "rap_id": job_request.identifier,
            "job_identifier": job1.identifier,
            "status": "succeeded",
        },
    )

    assert_log(
        debug_log_output.entries[1],
        {
            "event": "Newly completed job",
            "level": "debug",
            "job_identifier": job1.identifier,
        },
    )
    # running
    assert job2.identifier == "job2"
    assert job2.started_at == minutes_ago(now, 1)
    assert job2.updated_at == now
    assert job2.completed_at is None
    assert_log(
        debug_log_output.entries[2],
        {
            "event": "RAP Job Status",
            "level": "debug",
            "rap_id": job_request.identifier,
            "job_identifier": job2.identifier,
            "status": "running",
        },
    )
    # pending
    assert job3.identifier == "job3"
    assert job3.started_at is None
    assert job3.updated_at == now
    assert job3.completed_at is None
    assert_log(
        debug_log_output.entries[3],
        {
            "event": "RAP Job Status",
            "level": "debug",
            "rap_id": job_request.identifier,
            "job_identifier": job3.identifier,
            "status": "pending",
        },
    )

    assert spans[0].attributes["rap_status.affected_job_count"] == 3

    if pre_existing:
        assert (
            spans[0].attributes["rap_status.updated_job_identifiers"]
            == f"{job1.identifier},{job2.identifier},{job3.identifier}"
        )
        assert spans[0].attributes["rap_status.created_job_count"] == 0
        assert spans[0].attributes["rap_status.updated_job_count"] == 3
    else:
        assert (
            spans[0].attributes["rap_status.created_job_identifiers"]
            == f"{job1.identifier},{job2.identifier},{job3.identifier}"
        )
        assert spans[0].attributes["rap_status.created_job_count"] == 3
        assert spans[0].attributes["rap_status.updated_job_count"] == 0

    final_log = debug_log_output.entries[4]
    assert final_log["event"] == "Created or updated Jobs"
    action = "updated" if pre_existing else "created"
    assert final_log[f"{action}_job_ids"] == [job1.id, job2.id, job3.id]
    assert final_log[f"{action}_job_identifiers"] == [
        job1.identifier,
        job2.identifier,
        job3.identifier,
    ]

    check_job_request_status(job_request.identifier, JobRequestStatus.RUNNING)


@patch("jobserver.rap_api.status")
def test_update_jobs_multiple_job_requests(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    job_request1 = JobRequestFactory()
    job_request2 = JobRequestFactory()

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

    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": job1.identifier,
                "rap_id": job_request1.identifier,
                "action": "test-action1",
                "status": "succeeded",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30),
            },
            {
                "identifier": job2.identifier,
                "rap_id": job_request1.identifier,
                "action": "test-action2",
                "status": "running",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": None,
            },
            {
                "identifier": job3.identifier,
                "rap_id": job_request2.identifier,
                "action": "test-action2",
                "status": "running",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": None,
            },
            {
                "identifier": job4.identifier,
                "rap_id": job_request2.identifier,
                "action": "test-action3",
                "status": "pending",
                "created_at": minutes_ago(now, 2),
                "started_at": None,
                "completed_at": None,
            },
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 4 queries per job to update
    with django_assert_num_queries(18):
        rap.rap_status_update([job_request1.identifier, job_request2.identifier])

    # Check the command worked overall
    assert log_output.entries[-1]["event"] == "Created or updated Jobs"
    assert log_output.entries[-1]["updated_job_ids"] == [
        job1.id,
        job2.id,
        job3.id,
        job4.id,
    ]

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 4

    # Check the details of the jobs
    updated_job1, updated_job2, updated_job3, updated_job4 = jobs
    spans = get_trace()

    # job_request1 job succeeded
    assert updated_job1.identifier == job1.identifier
    assert updated_job1.started_at == minutes_ago(now, 1)
    assert updated_job1.updated_at == now
    assert updated_job1.completed_at == seconds_ago(now, 30)
    assert updated_job1.metrics == {"cpu_peak": 99}

    # job_request2 job running
    assert updated_job2.identifier == job2.identifier
    assert updated_job2.started_at == minutes_ago(now, 1)
    assert updated_job2.updated_at == now
    assert updated_job2.completed_at is None

    # job_request3 job running
    assert updated_job3.identifier == job3.identifier
    assert updated_job3.started_at == minutes_ago(now, 1)
    assert updated_job3.updated_at == now
    assert updated_job3.completed_at is None

    # job_request4 job pending
    assert updated_job4.identifier == job4.identifier
    assert updated_job4.started_at is None
    assert updated_job4.updated_at == now
    assert updated_job4.completed_at is None

    assert (
        spans[0].attributes["rap_status.updated_job_identifiers"]
        == f"{job1.identifier},{job2.identifier},{job3.identifier},{job4.identifier}"
    )
    assert spans[0].attributes["rap_status.affected_job_count"] == 4
    assert spans[0].attributes["rap_status.created_job_count"] == 0
    assert spans[0].attributes["rap_status.updated_job_count"] == 4

    check_job_request_status(job_request1.identifier, JobRequestStatus.RUNNING)
    check_job_request_status(job_request2.identifier, JobRequestStatus.RUNNING)


@patch("jobserver.rap_api.status")
def test_unexpected_local_jobs(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    job_request = JobRequestFactory()

    jobs = JobFactory.create_batch(
        2,
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )

    assert Job.objects.count() == 2

    # rap/status only returns one job of the two created
    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": jobs[0].identifier,
                "rap_id": job_request.identifier,
                "status": "succeeded",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30),
            }
        ],
        [],
        now,
    )

    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 4 queries per job to update
    with django_assert_num_queries(6):
        rap.rap_status_update([job_request.identifier])

    # Unexpected lobs are not deleted
    jobs = Job.objects.all()
    assert jobs.count() == 2

    assert log_output.entries[-2]["event"] == "Created or updated Jobs"
    assert log_output.entries[-2]["updated_job_ids"] == [jobs[0].id]

    assert log_output.entries[-1]["level"] == "error"
    assert (
        log_output.entries[-1]["event"]
        == "Locally existing jobs missing from RAP API response"
    )
    assert log_output.entries[-1]["unrecognised_job_identifiers"] == [
        jobs[1].identifier
    ]

    spans = get_trace()
    assert (
        spans[0].attributes["rap_status.updated_job_identifiers"] == jobs[0].identifier
    )
    assert (
        spans[0].attributes["rap_status.unrecognised_job_identifiers"]
        == jobs[1].identifier
    )
    assert spans[0].attributes["rap_status.affected_job_count"] == 1
    assert spans[0].attributes["rap_status.created_job_count"] == 0
    assert spans[0].attributes["rap_status.updated_job_count"] == 1

    check_job_request_status(job_request.identifier, JobRequestStatus.RUNNING)


@patch("jobserver.rap_api.status")
def test_flip_flop_updates(mock_rap_api_status, log_output, now):
    job_request = JobRequestFactory()

    job = JobFactory.create(
        job_request=job_request,
        started_at=None,
        status="pending",
        completed_at=None,
    )
    test_job_id = job.id

    test_response_json_stale = rap_status_response_factory(
        [
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
                "status": "running",
                "created_at": minutes_ago(now, 1),
                "started_at": now,
                "completed_at": None,
            }
        ],
        [],
        now,
    )
    test_response_json_fresh = rap_status_response_factory(
        [
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
                "status": "succeeded",
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30),
            }
        ],
        [],
        now,
    )

    # The rap_status command will modify the returned dict in place,
    # so use a deepcopy so that our test will work as expected!
    mock_rap_api_status.return_value = deepcopy(test_response_json_stale)
    rap.rap_status_update([job_request.identifier])

    job = Job.objects.get(id=test_job_id)
    assert job.status == "running"
    check_job_request_status(job_request.identifier, JobRequestStatus.RUNNING)

    mock_rap_api_status.return_value = deepcopy(test_response_json_fresh)
    rap.rap_status_update([job_request.identifier])
    job = Job.objects.get(id=test_job_id)
    assert job.status == "succeeded"
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)

    mock_rap_api_status.return_value = deepcopy(test_response_json_stale)
    rap.rap_status_update([job_request.identifier])
    job = Job.objects.get(id=test_job_id)
    assert job.status == "running"
    # Once a JobRequest hits a completed state, it stays there
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)

    mock_rap_api_status.return_value = deepcopy(test_response_json_fresh)
    rap.rap_status_update([job_request.identifier])
    job = Job.objects.get(id=test_job_id)
    assert job.status == "succeeded"
    check_job_request_status(job_request.identifier, JobRequestStatus.SUCCEEDED)

    for span in get_trace():
        assert span.attributes["rap_status.updated_job_identifiers"] == job.identifier
        assert span.attributes["rap_status.affected_job_count"] == 1
        assert span.attributes["rap_status.created_job_count"] == 0
        assert span.attributes["rap_status.updated_job_count"] == 1


@patch("jobserver.rap_api.status")
def test_rap_status_update_unrecognised_rap_ids(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    job_request = JobRequestFactory(_status=JobRequestStatus.PENDING)

    # RAP controller returns no jobs and unrecognised rap id
    test_response_json = rap_status_response_factory(
        [],
        [job_request.identifier],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    with django_assert_num_queries(2):
        rap.rap_status_update([job_request.identifier])

    # no change to jobs
    assert not Job.objects.exists()
    check_job_request_status(job_request.identifier, JobRequestStatus.PENDING)

    assert log_output.entries[-1]["event"] == "Unrecognised RAP ids"
    assert log_output.entries[-1]["level"] == "warning"
    assert log_output.entries[-1]["rap_ids"] == [job_request.identifier]

    spans = get_trace()
    assert (
        spans[0].attributes["rap_status.unrecognised_rap_ids"] == job_request.identifier
    )


@patch("jobserver.rap_api.status")
def test_rap_status_update_unrecognised_rap_ids_job_request_with_unknown_created_error(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    # Create a job request that encountered a RapAPIRequestError while trying to
    # create jobs on the controller. For a job request with this status, we don't know
    # yet if jobs were created on the controller or not
    job_request = JobRequestFactory(
        _status=JobRequestStatus.UNKNOWN_ERROR_CREATING_JOBS
    )

    # RAP controller returns no jobs and unrecognised rap id
    test_response_json = rap_status_response_factory(
        [],
        [job_request.identifier],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1 & 2) Get all matching job requests, prefetching jobs
    # 3) Update the failed job request status
    with django_assert_num_queries(3):
        rap.rap_status_update([job_request.identifier])

    # no new jobs
    assert not Job.objects.exists()
    # The job request has been marked as failed
    job_request = check_job_request_status(
        job_request.identifier, JobRequestStatus.FAILED
    )
    assert job_request.status_message == "Unknown error creating jobs"

    # We still log the unrecognised rap ids
    assert log_output.entries[-2]["event"] == "Unrecognised RAP ids"
    assert log_output.entries[-2]["level"] == "warning"
    assert log_output.entries[-2]["rap_ids"] == [job_request.identifier]

    assert (
        log_output.entries[-1]["event"]
        == "Job requests with no RAP jobs updated to failed"
    )
    assert log_output.entries[-1]["level"] == "info"
    assert log_output.entries[-1]["rap_ids"] == [job_request.identifier]

    spans = get_trace()
    assert (
        spans[0].attributes["rap_status.unrecognised_rap_ids"] == job_request.identifier
    )
    assert spans[0].attributes["rap_status.failed_rap_ids"] == job_request.identifier


@patch("jobserver.rap_api.status")
def test_rap_status_update_unknown_job_request(
    mock_rap_api_status, log_output, django_assert_num_queries, now
):
    # RAP controller returns a job with an unrecognised rap id
    test_response_json = rap_status_response_factory(
        [{"identifier": "job-identifier"}],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    # Queries:
    # 1) Get all matching job requests, no jobs to prefetch
    with django_assert_num_queries(1):
        rap.rap_status_update(["unknown-rap-id"])

    # no change to jobs
    assert not Job.objects.exists()

    assert log_output.entries[-1]["event"] == "Job-server does not recognise RAP id"
    assert log_output.entries[-1]["level"] == "warning"
    assert log_output.entries[-1]["rap_id"] == "unknown-rap-id"

    spans = get_trace()
    assert spans[0].attributes == {}


@pytest.mark.parametrize(
    "notifcations_on,new_status,notify_expected",
    [
        (True, "running", False),
        (True, "succeeded", True),
        (False, "running", False),
        (False, "succeeded", False),
    ],
)
@patch("jobserver.rap_api.status")
def test_rap_status_update_notifications(
    mock_rap_api_status, now, mocker, notifcations_on, new_status, notify_expected
):
    """
    Test that notifications are only sent for job requests with notifications
    turned on, and only for job requests that have just completed
    """
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=notifcations_on)
    job = JobFactory(job_request=job_request, status="running")

    test_response_json = rap_status_response_factory(
        [
            {
                "identifier": job.identifier,
                "rap_id": job_request.identifier,
                "status": new_status,
                "created_at": minutes_ago(now, 2),
                "started_at": minutes_ago(now, 1),
                "completed_at": seconds_ago(now, 30)
                if new_status == "succeeded"
                else None,
            }
        ],
        [],
        now,
    )
    mock_rap_api_status.return_value = test_response_json

    mocked_send = mocker.patch(
        "jobserver.api.jobs.send_finished_notification", autospec=True
    )

    rap.rap_status_update([job_request.identifier])

    if notify_expected:
        mocked_send.assert_called_once()
    else:
        mocked_send.assert_not_called()
