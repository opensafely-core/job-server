from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated

from jobserver.api import (
    JobAPIUpdate,
    JobRequestAPIList,
    WorkspaceStatusesAPI,
    get_backend_from_token,
    update_stats,
)
from jobserver.models import Backend, Job, JobRequest, Stats

from ..factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    StatsFactory,
    WorkspaceFactory,
)


def test_token_backend_empty_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token(None)


def test_token_backend_no_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("")


@pytest.mark.django_db
def test_token_backend_success(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    tpp = Backend.objects.get(name="tpp")

    assert get_backend_from_token(tpp.auth_token) == tpp


@pytest.mark.django_db
def test_token_backend_unknown_backend():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("test")


@pytest.mark.django_db
def test_update_stats_existing_url():
    backend = BackendFactory()
    StatsFactory(backend=backend, url="test")

    update_stats(backend, url="test")

    # check there's only one Stats for backend
    assert backend.stats.count() == 1
    assert backend.stats.first().url == "test"


@pytest.mark.django_db
def test_update_stats_new_url():
    backend = BackendFactory()
    StatsFactory(backend=backend, url="test")

    update_stats(backend, url="new-url")

    # check there's only one Stats for backend
    assert backend.stats.count() == 2
    assert backend.stats.last().url == "new-url"


@pytest.mark.django_db
def test_jobapiupdate_all_existing(api_rf, freezer):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    # 3 pending jobs already exist
    job1, job2, job3, = JobFactory.create_batch(
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

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test-action1",
            "status": "succeeded",
            "status_code": "",
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
            "status_code": "",
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
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": None,
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
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
    backend = BackendFactory()
    job_request = JobRequestFactory()

    assert Job.objects.count() == 0

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test-action",
            "status": "running",
            "status_code": "",
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
            "status_code": "",
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
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": None,
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 3


@pytest.mark.django_db
def test_jobapiupdate_invalid_payload(api_rf):
    backend = BackendFactory()

    assert Job.objects.count() == 0

    data = [{"action": "test-action"}]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert Job.objects.count() == 0

    assert response.status_code == 400, response.data

    errors = response.data[0]
    assert len(errors.keys()) == 9


@pytest.mark.django_db
def test_jobapiupdate_is_behind_auth(api_rf):
    request = api_rf.post("/")
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 403, response.data


@pytest.mark.django_db
def test_jobapiupdate_mixture(api_rf, freezer):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    # pending
    job1 = JobFactory(
        job_request=job_request,
        identifier="job1",
        action="test",
        started_at=None,
        completed_at=None,
    )

    job2 = JobFactory(
        job_request=job_request,
        identifier="job2",
        action="test",
        started_at=None,
        completed_at=None,
    )

    assert Job.objects.count() == 2

    data = [
        {
            "identifier": "job2",
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": timezone.now() - timedelta(seconds=30),
        },
        {
            "identifier": "job3",
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "running",
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        },
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data

    # we shouldn't have a different number of jobs
    jobs = Job.objects.all()
    assert len(jobs) == 2

    # check our jobs look as expected
    job2, job3 = jobs

    # succeeded
    assert job2.pk == job2.pk
    assert job2.identifier == "job2"
    assert job2.started_at == timezone.now() - timedelta(minutes=1)
    assert job2.updated_at == timezone.now()
    assert job2.completed_at == timezone.now() - timedelta(seconds=30)

    # running
    assert job3.pk != job1.pk
    assert job3.pk != job2.pk
    assert job3.identifier == "job3"
    assert job3.started_at == timezone.now() - timedelta(minutes=1)
    assert job3.updated_at == timezone.now()
    assert job3.completed_at is None


@pytest.mark.django_db
def test_jobapiupdate_notifications_on_with_move_to_finished(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=True)
    job = JobFactory(job_request=job_request, status="running")

    data = [
        {
            "identifier": job.identifier,
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": timezone.now() - timedelta(seconds=30),
        },
    ]

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=job_request.backend.auth_token,
        data=data,
        format="json",
    )
    with patch("jobserver.api.send_finished_notification") as mocked_send:
        response = JobAPIUpdate.as_view()(request)

    mocked_send.assert_called_once()
    assert response.status_code == 200


@pytest.mark.django_db
def test_jobapiupdate_notifications_on_without_move_to_finished(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=True)
    job = JobFactory(job_request=job_request, status="succeeded")

    data = [
        {
            "identifier": job.identifier,
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": timezone.now() - timedelta(seconds=30),
        },
    ]

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=job_request.backend.auth_token,
        data=data,
        format="json",
    )
    with patch("jobserver.api.send_finished_notification") as mocked_send:
        response = JobAPIUpdate.as_view()(request)

    mocked_send.assert_not_called()
    assert response.status_code == 200


@pytest.mark.django_db
def test_jobapiupdate_post_only(api_rf):
    backend = BackendFactory()

    # GET
    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # HEAD
    request = api_rf.head("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # PATCH
    request = api_rf.patch("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert JobAPIUpdate.as_view()(request).status_code == 405

    # PUT
    request = api_rf.put("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert JobAPIUpdate.as_view()(request).status_code == 405


@pytest.mark.django_db
def test_jobapiupdate_unknown_job_request(api_rf):
    backend = BackendFactory()
    JobRequestFactory()

    data = [
        {
            "identifier": "job1",
            "job_request_id": "test",
            "action": "test-action",
            "status": "running",
            "status_code": "",
            "status_message": "",
            "created_at": timezone.now() - timedelta(minutes=2),
            "started_at": timezone.now() - timedelta(minutes=1),
            "updated_at": timezone.now(),
            "completed_at": None,
        }
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 400, response.data
    assert "Unknown JobRequest IDs" in response.data[0]


@pytest.mark.django_db
def test_jobrequestapilist_filter_by_backend(api_rf):
    JobRequestFactory(backend=Backend.objects.get(name="expectations"))
    JobRequestFactory(backend=BackendFactory(name="test"))

    request = api_rf.get("/?backend=expectations")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200, response.data
    assert len(response.data["results"]) == 1


def test_jobrequestapilist_get_only(api_rf):
    request = api_rf.post("/", data={}, format="json")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 405


@pytest.mark.django_db
def test_jobrequestapilist_produce_stats_when_authed(api_rf):
    backend = BackendFactory()

    assert Stats.objects.filter(backend=backend).count() == 0

    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200
    assert Stats.objects.filter(backend=backend).count() == 1


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


@pytest.mark.django_db
def test_workspacestatusesapi_success(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request, action="run_all", status="failed")

    request = api_rf.get("/")
    response = WorkspaceStatusesAPI.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert response.data["run_all"] == "failed"


@pytest.mark.django_db
def test_workspacestatusesapi_unknown_workspace(api_rf):
    request = api_rf.get("/")
    response = WorkspaceStatusesAPI.as_view()(request, name="test")
    assert response.status_code == 404
