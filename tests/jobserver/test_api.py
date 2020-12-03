from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import force_authenticate

from jobserver.api import JobAPIUpdate, JobRequestAPIList
from jobserver.models import Job, JobRequest

from ..factories import JobFactory, JobRequestFactory, UserFactory, WorkspaceFactory


@pytest.mark.django_db
def test_jobapiupdate_all_existing(api_rf, freezer):
    job_request = JobRequestFactory()

    # 3 pending jobs already exist
    job1, job2, job3, = JobFactory.create_batch(
        3,
        job_request=job_request,
        started=False,
        started_at=None,
        completed_at=None,
    )
    job1.identifier = "job1"
    job1.save()

    job2.identifier = "job2"
    job2.save()

    job3.identifier = "job3"
    job3.save()

    assert Job.objects.count() == 3

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test-action1",
            "status": "succeeded",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": timezone.now() - timedelta(seconds=30),
        },
        {
            "identifier": "job2",
            "job_request_id": job_request.identifier,
            "action": "test-action2",
            "status": "running",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        },
        {
            "identifier": "job3",
            "job_request_id": job_request.identifier,
            "action": "test-action3",
            "status": "pending",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": None,
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory())
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 3

    # check our jobs look as expected
    job1, job2, job3 = jobs

    # succeeded
    assert job1.identifier == "job1"
    assert job1.started_at == timezone.now() - timedelta(minutes=1)
    assert job1.updated_at == timezone.now()
    assert job1.completed_at == timezone.now() - timedelta(seconds=30)

    # running
    assert job2.identifier == "job2"
    assert job2.started_at == timezone.now() - timedelta(minutes=1)
    assert job2.updated_at == timezone.now()
    assert job2.completed_at is None

    # pending
    assert job3.identifier == "job3"
    assert job3.started_at is None
    assert job3.updated_at == timezone.now()
    assert job3.completed_at is None


@pytest.mark.django_db
def test_jobapiupdate_all_new(api_rf):
    job_request = JobRequestFactory()

    assert Job.objects.count() == 0

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test-action",
            "status": "running",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        },
        {
            "identifier": "job2",
            "action": "test-action",
            "job_request_id": job_request.identifier,
            "status": "pending",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "updated_at": timezone.now(),
            "started_at": None,
            "completed_at": None,
        },
        {
            "identifier": "job3",
            "job_request_id": job_request.identifier,
            "action": "test-action",
            "status": "running",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": None,
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory())
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 3


@pytest.mark.django_db
def test_jobapiupdate_invalid_payload(api_rf):
    assert Job.objects.count() == 0

    data = [{"action": "test-action"}]

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory())
    response = JobAPIUpdate.as_view()(request)

    assert Job.objects.count() == 0

    assert response.status_code == 400, response.data

    errors = response.data[0]
    assert len(errors.keys()) == 8


@pytest.mark.django_db
def test_jobapiupdate_is_behind_auth(api_rf):
    request = api_rf.post("/")
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 401, response.data


@pytest.mark.django_db
def test_jobapiupdate_mixture(api_rf, freezer):
    job_request = JobRequestFactory()

    # pending
    job1 = JobFactory(
        job_request=job_request,
        identifier="job1",
        action="test",
        started_at=None,
        completed_at=None,
    )

    assert Job.objects.count() == 1

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": timezone.now() - timedelta(seconds=30),
        },
        {
            "identifier": "job2",
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "running",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory())
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 2

    # check our jobs look as expected
    job2, job3 = jobs

    # succeeded
    assert job2.pk == job1.pk
    assert job2.identifier == "job1"
    assert job2.started_at == timezone.now() - timedelta(minutes=1)
    assert job2.updated_at == timezone.now()
    assert job2.completed_at == timezone.now() - timedelta(seconds=30)

    # running
    assert job3.pk != job1.pk
    assert job3.identifier == "job2"
    assert job3.started_at == timezone.now() - timedelta(minutes=1)
    assert job3.updated_at == timezone.now()
    assert job3.completed_at is None


@pytest.mark.django_db
def test_jobapiupdate_post_only(api_rf):
    # GET
    request = api_rf.get("/")
    force_authenticate(request, user=UserFactory())
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # HEAD
    request = api_rf.head("/")
    force_authenticate(request, user=UserFactory())
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # PATCH
    request = api_rf.patch("/")
    force_authenticate(request, user=UserFactory())
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # PUT
    request = api_rf.put("/")
    force_authenticate(request, user=UserFactory())
    assert JobAPIUpdate.as_view()(request).status_code == 405


@pytest.mark.django_db
def test_jobapiupdate_unknown_job_request(api_rf):
    JobRequestFactory()

    data = [
        {
            "identifier": "job1",
            "job_request_id": "test",
            "action": "test-action",
            "status": "running",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        }
    ]

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory())
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 400, response.data
    assert "Unknown JobRequest IDs" in response.data[0]


@pytest.mark.django_db
def test_jobrequestapilist_filter_by_backend(api_rf):
    JobRequestFactory(backend="expectations")
    JobRequestFactory(backend="test")

    request = api_rf.get("/?backend=expectations")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200
    assert len(response.data["results"]) == 1


def test_jobrequestapilist_get_only(api_rf):
    request = api_rf.post("/", data={}, format="json")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 405


@pytest.mark.django_db
def test_jobrequestapilist_success(api_rf):
    workspace = WorkspaceFactory()

    # all completed
    job_request1 = JobRequestFactory(workspace=workspace)
    JobFactory.create_batch(2, job_request=job_request1, completed_at=timezone.now())

    # some completed
    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, completed_at=timezone.now())
    JobFactory(job_request=job_request2, completed_at=None)

    # none completed
    job_request3 = JobRequestFactory(workspace=workspace)
    JobFactory.create_batch(2, job_request=job_request3, completed_at=None)

    #  no jobs
    job_request4 = JobRequestFactory(workspace=workspace)

    assert JobRequest.objects.count() == 4

    request = api_rf.get("/")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200
    assert response.data["count"] == 3
    assert len(response.data["results"]) == 3

    identifiers = {j["identifier"] for j in response.data["results"]}
    assert identifiers == {
        job_request2.identifier,
        job_request3.identifier,
        job_request4.identifier,
    }
