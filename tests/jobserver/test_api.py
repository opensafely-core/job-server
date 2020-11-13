from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import force_authenticate

from jobserver.api import JobAPIUpdate, JobRequestAPIList, JobViewSet
from jobserver.models import Job, JobRequest

from ..factories import (
    JobFactory,
    JobOutputFactory,
    JobRequestFactory,
    UserFactory,
    WorkspaceFactory,
)


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
    assert job2.pk != job1.pk
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
    JobRequestFactory(backend="tpp")
    JobRequestFactory(backend="test")

    request = api_rf.get("/?backend=tpp")
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


@pytest.mark.django_db
def test_jobviewset_create_success(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, backend="tpp")
    job1 = JobFactory(job_request=job_request, action="test-action1")

    job2 = JobFactory(job_request=job_request, action="test-action2")
    job1.needed_by = job2
    job1.save()

    job3 = JobFactory(job_request=job_request, action="test-action3")
    job2.needed_by = job3
    job2.save()

    data = {
        "force_run": True,
        "force_run_dependencies": True,
        "action_id": "frob",
        "backend": "tpp",
        "needed_by_id": job1.pk,
        "workspace_id": workspace.pk,
    }

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"post": "create"})(request)

    assert response.status_code == 201, response.data

    assert response.data["action_id"] == "frob"
    assert response.data["backend"] == "tpp"
    assert response.data["force_run"]
    assert response.data["needed_by_id"] == job1.pk
    assert response.data["workspace_id"] == workspace.pk


@pytest.mark.django_db
def test_jobviewset_create_with_unknown_job(api_rf):
    workspace = WorkspaceFactory()

    data = {
        "force_run": True,
        "force_run_dependencies": True,
        "action_id": "frob",
        "backend": "tpp",
        "needed_by_id": 0,
        "workspace_id": workspace.pk,
    }

    request = api_rf.post("/", data=data, format="json")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"post": "create"})(request)

    assert response.status_code == 400, response.data

    error = ErrorDetail("needed_by_id must be a valid Job ID", code="invalid")
    assert response.data == [error]


@pytest.mark.django_db
def test_jobviewset_filter_action(api_rf):
    job1 = JobFactory(action="action1")
    JobFactory(action="action2")

    request = api_rf.get("/?action_id=action1")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert response.data["results"][0]["pk"] == job1.pk


@pytest.mark.django_db
def test_jobviewset_filter_backend(api_rf):
    job1 = JobFactory(job_request=JobRequestFactory(backend="tpp"))
    JobFactory(job_request=JobRequestFactory(backend="emis"))

    request = api_rf.get("/?backend=tpp")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert response.data["results"][0]["pk"] == job1.pk


@pytest.mark.django_db
def test_jobviewset_filter_needed_by_id(api_rf):
    job1 = JobFactory(job_request=JobRequestFactory(backend="tpp"))
    job2 = JobFactory(job_request=JobRequestFactory(backend="emis"))

    job1.needed_by = job2
    job1.save()

    request = api_rf.get(f"/?needed_by_id={job2.pk}")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert response.data["results"][0]["pk"] == job1.pk


@pytest.mark.django_db
def test_jobviewset_filter_started(api_rf):
    job1 = JobFactory(started=True)
    JobFactory(started=False)

    request = api_rf.get("/?started=True")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert response.data["results"][0]["pk"] == job1.pk


@pytest.mark.django_db
def test_jobviewset_filter_workspace(api_rf):
    workspace1 = WorkspaceFactory()
    job_request1 = JobRequestFactory(workspace=workspace1)
    job1 = JobFactory(job_request=job_request1)

    workspace2 = WorkspaceFactory()
    job_request2 = JobRequestFactory(workspace=workspace2)
    JobFactory(job_request=job_request2)

    request = api_rf.get(f"/?workspace={workspace1.pk}")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    assert response.data["results"][0]["pk"] == job1.pk


@pytest.mark.django_db
def test_jobviewset_list_success(api_rf):
    workspace = WorkspaceFactory(
        branch="master",
        db="dummy",
        name="households",
        repo="https://github.com/test/test",
        created_by=UserFactory(username="test-user"),
    )
    job_request = JobRequestFactory(workspace=workspace, backend="tpp")
    JobFactory(
        job_request=job_request,
        action="test-action",
        force_run=True,
        started=True,
        status_code=2,
        status_message="Danger Will Robinson",
    )

    request = api_rf.get("/")
    force_authenticate(request, user=UserFactory())
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    job = dict(response.data["results"][0])

    keys = [
        "url",
        "pk",
        "backend",
        "started",
        "force_run",
        "force_run_dependencies",
        "action_id",
        "status_code",
        "status_message",
        "outputs",
        "needed_by_id",
        "workspace",
        "workspace_id",
        "created_at",
        "started_at",
        "completed_at",
        "callback_url",
    ]
    assert list(job.keys()) == keys

    assert job["url"] == f"http://testserver/api/v1/jobs/{job['pk']}/"
    assert job["pk"] == 1
    assert job["backend"] == "tpp"
    assert job["started"]
    assert job["force_run"]
    assert not job["force_run_dependencies"]
    assert job["action_id"] == "test-action"
    assert job["status_code"] == 2
    assert job["status_message"] == "Danger Will Robinson"
    assert job["outputs"] == []
    assert job["needed_by_id"] is None
    assert job["workspace_id"] == 1
    assert job["callback_url"] == ""

    workspace = dict(job["workspace"])

    keys = ["id", "url", "name", "repo", "branch", "db", "owner", "created_at"]
    assert list(workspace.keys()) == keys

    assert workspace["id"] == 1
    assert workspace["url"] == f"http://testserver/api/v1/workspaces/{workspace['id']}/"
    assert workspace["name"] == "households"
    assert workspace["repo"] == "https://github.com/test/test"
    assert workspace["branch"] == "master"
    assert workspace["db"] == "dummy"
    assert workspace["owner"] == "test-user"


@pytest.mark.django_db
def test_jobviewset_list_with_filters_success(api_rf):
    workspace1 = WorkspaceFactory()
    workspace2 = WorkspaceFactory()

    job_request1 = JobRequestFactory(workspace=workspace1, backend="emis")
    job_request2 = JobRequestFactory(workspace=workspace2, backend="tpp")

    JobFactory(job_request=job_request1, force_run=False, action="attack")
    JobFactory(job_request=job_request1, force_run=True, action="cast")
    JobFactory(job_request=job_request1, force_run=False, action="dash")
    JobFactory(job_request=job_request2, force_run=True, action="disengage")
    JobFactory(job_request=job_request2, force_run=False, action="dodge")
    JobFactory(job_request=job_request2, force_run=True, action="help")

    params = {
        "action_id": "dodge",
        "backend": "tpp",
        "workspace_id": workspace2.pk,
        "limit": 1,
    }
    request = api_rf.get("/", params)
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"get": "list"})(request)

    assert response.status_code == 200

    assert response.data["count"] == 1

    job = response.data["results"][0]
    assert job["action_id"] == "dodge"
    assert job["backend"] == "tpp"
    assert not job["force_run"]


@pytest.mark.django_db
def test_jobviewset_update_success(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, backend="tpp")
    job = JobFactory(job_request=job_request, action="test-action", force_run=False)

    assert job.status_code is None
    assert job.status_message == ""

    data = {
        "action_id": job.action,
        "backend": job.job_request.backend,
        "force_run": True,
        "force_run_dependencies": job.job_request.force_run_dependencies,
        "needed_by_id": None,
        "status_code": -2,
        "status_message": "Docker never started",
        "outputs": [{"location": "/some/path"}],
    }
    request = api_rf.patch("/", data=data, format="json")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"patch": "update"})(request, pk=job.pk)

    assert response.status_code == 200, response.data

    job.refresh_from_db()

    assert job.force_run
    assert job.status_code == -2
    assert job.status_message == "Docker never started"


@pytest.mark.django_db
def test_jobviewset_update_with_outputs_and_existing_outputs_fails(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, backend="tpp")
    job = JobFactory(job_request=job_request, action="test-action", force_run=False)
    JobOutputFactory(job=job)

    assert job.status_code is None
    assert job.status_message == ""

    data = {
        "action_id": job.action,
        "backend": job.job_request.backend,
        "force_run": True,
        "force_run_dependencies": job.job_request.force_run_dependencies,
        "needed_by_id": None,
        "status_code": -2,
        "status_message": "Docker never started",
        "outputs": [{"location": "test"}],
    }
    request = api_rf.patch("/", data=data, format="json")
    force_authenticate(request, user=UserFactory(is_superuser=True))
    response = JobViewSet.as_view(actions={"patch": "update"})(request, pk=job.pk)

    assert response.status_code == 400
    error = ErrorDetail("You can only set outputs for a job once", code="invalid")
    assert response.data == [error]
