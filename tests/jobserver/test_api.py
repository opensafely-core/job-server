import pytest
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import force_authenticate

from jobserver.api import JobViewSet

from ..factories import (
    JobFactory,
    JobOutputFactory,
    JobRequestFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.mark.django_db
def test_jobviewset_create_success(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, backend="tpp")
    job1 = JobFactory(job_request=job_request, action_id="test-action1")

    job2 = JobFactory(job_request=job_request, action_id="test-action2")
    job1.needed_by = job2
    job1.save()

    job3 = JobFactory(job_request=job_request, action_id="test-action3")
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
        action_id="test-action",
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

    assert job["url"] == f"http://testserver/api/jobs/{job['pk']}/"
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
    assert job["callback_url"] is None

    workspace = dict(job["workspace"])

    keys = ["id", "url", "name", "repo", "branch", "db", "owner", "created_at"]
    assert list(workspace.keys()) == keys

    assert workspace["id"] == 1
    assert workspace["url"] == f"http://testserver/api/workspaces/{workspace['id']}/"
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

    JobFactory(job_request=job_request1, force_run=False, action_id="attack")
    JobFactory(job_request=job_request1, force_run=True, action_id="cast")
    JobFactory(job_request=job_request1, force_run=False, action_id="dash")
    JobFactory(job_request=job_request2, force_run=True, action_id="disengage")
    JobFactory(job_request=job_request2, force_run=False, action_id="dodge")
    JobFactory(job_request=job_request2, force_run=True, action_id="help")

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
    job = JobFactory(job_request=job_request, action_id="test-action", force_run=False)

    assert job.status_code is None
    assert job.status_message is None

    data = {
        "action_id": job.action_id,
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
    job = JobFactory(job_request=job_request, action_id="test-action", force_run=False)
    JobOutputFactory(job=job)

    assert job.status_code is None
    assert job.status_message is None

    data = {
        "action_id": job.action_id,
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
