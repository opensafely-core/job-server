import pytest
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated

from jobserver.api.jobs import (
    JobAPIUpdate,
    JobRequestAPIList,
    UserAPIDetail,
    WorkspaceStatusesAPI,
    get_backend_from_token,
    update_stats,
)
from jobserver.authorization import CoreDeveloper, OrgCoordinator, ProjectDeveloper
from jobserver.models import Job, JobRequest, Stats
from tests.factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    StatsFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.utils import minutes_ago, seconds_ago


def test_token_backend_empty_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token(None)


def test_token_backend_no_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("")


def test_token_backend_success():
    backend = BackendFactory(slug="tpp")

    assert get_backend_from_token(backend.auth_token) == backend


def test_token_backend_unknown_backend():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("test")


def test_update_stats_existing_url():
    backend = BackendFactory()
    StatsFactory(backend=backend, url="test")

    update_stats(backend, url="test")

    # check there's only one Stats for backend
    assert backend.stats.count() == 1
    assert backend.stats.first().url == "test"


def test_update_stats_new_url():
    backend = BackendFactory()
    StatsFactory(backend=backend, url="test")

    update_stats(backend, url="new-url")

    # check there's only one Stats for backend
    assert backend.stats.count() == 2
    assert backend.stats.last().url == "new-url"


def test_jobapiupdate_all_existing(api_rf, freezer):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    now = timezone.now()

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
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": seconds_ago(now, 30),
        },
        {
            "identifier": "job2",
            "job_request_id": job_request.identifier,
            "action": "test-action2",
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
            "job_request_id": job_request.identifier,
            "action": "test-action3",
            "status": "pending",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": None,
            "updated_at": now,
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
    assert job1.started_at == minutes_ago(now, 1)
    assert job1.updated_at == now
    assert job1.completed_at == seconds_ago(now, 30)

    # running
    assert job2.identifier == "job2"
    assert job2.started_at == minutes_ago(now, 1)
    assert job2.updated_at == now
    assert job2.completed_at is None

    # pending
    assert job3.identifier == "job3"
    assert job3.started_at is None
    assert job3.updated_at == now
    assert job3.completed_at is None


def test_jobapiupdate_all_new(api_rf):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    now = timezone.now()

    assert Job.objects.count() == 0

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "test-action",
            "status": "running",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": None,
        },
        {
            "identifier": "job2",
            "action": "test-action",
            "job_request_id": job_request.identifier,
            "status": "pending",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "updated_at": now,
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
            "created_at": minutes_ago(now, 2),
            "started_at": None,
            "updated_at": now,
            "completed_at": None,
        },
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 3


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


def test_jobapiupdate_is_behind_auth(api_rf):
    request = api_rf.post("/")
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 403, response.data


def test_jobapiupdate_mixture(api_rf, freezer):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    now = timezone.now()

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
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": seconds_ago(now, 30),
        },
        {
            "identifier": "job3",
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "running",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
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
    assert job2.started_at == minutes_ago(now, 1)
    assert job2.updated_at == now
    assert job2.completed_at == seconds_ago(now, 30)

    # running
    assert job3.pk != job1.pk
    assert job3.pk != job2.pk
    assert job3.identifier == "job3"
    assert job3.started_at == minutes_ago(now, 1)
    assert job3.updated_at == now
    assert job3.completed_at is None


def test_jobapiupdate_notifications_on_with_move_to_completed(api_rf, mocker):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=True)
    job = JobFactory(job_request=job_request, status="running")

    now = timezone.now()

    mocked_send = mocker.patch(
        "jobserver.api.jobs.send_finished_notification", autospec=True
    )

    data = [
        {
            "identifier": job.identifier,
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": seconds_ago(now, 30),
        },
    ]
    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=job_request.backend.auth_token,
        data=data,
        format="json",
    )

    response = JobAPIUpdate.as_view()(request)

    mocked_send.assert_called_once()
    assert response.status_code == 200


def test_jobapiupdate_notifications_on_without_move_to_completed(api_rf, mocker):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=True)
    job = JobFactory(job_request=job_request, status="succeeded")

    now = timezone.now()

    mocked_send = mocker.patch(
        "jobserver.api.jobs.send_finished_notification", autospec=True
    )

    data = [
        {
            "identifier": job.identifier,
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "succeeded",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": seconds_ago(now, 30),
        },
    ]
    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=job_request.backend.auth_token,
        data=data,
        format="json",
    )

    response = JobAPIUpdate.as_view()(request)

    mocked_send.assert_not_called()
    assert response.status_code == 200


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


def test_jobapiupdate_post_with_internal_error(api_rf, mocker):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    now = timezone.now()

    mocked_sentry_sdk = mocker.patch("jobserver.api.jobs.sentry_sdk", autospec=True)

    data = [
        {
            "identifier": "job",
            "job_request_id": job_request.identifier,
            "action": "test-action",
            "status": "running",
            "status_code": "",
            "status_message": "Running",
            "created_at": now,
            "started_at": now,
            "updated_at": now,
            "completed_at": None,
        },
    ]
    request_1 = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    JobAPIUpdate.as_view()(request_1)

    data[0]["status_message"] = "Internal error"
    request_2 = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request_2)

    assert response.status_code == 200, response.data

    mocked_sentry_sdk.capture_message.assert_called_once()


def test_jobapiupdate_unknown_job_request(api_rf):
    backend = BackendFactory()
    JobRequestFactory()

    now = timezone.now()

    data = [
        {
            "identifier": "job1",
            "job_request_id": "test",
            "action": "test-action",
            "status": "running",
            "status_code": "",
            "status_message": "",
            "created_at": minutes_ago(now, 2),
            "started_at": minutes_ago(now, 1),
            "updated_at": now,
            "completed_at": None,
        }
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view()(request)

    assert response.status_code == 400, response.data
    assert "Unknown JobRequest IDs" in response.data[0]


def test_jobrequestapilist_filter_by_backend(api_rf):
    backend = BackendFactory()
    JobRequestFactory(backend=backend)
    JobRequestFactory()

    request = api_rf.get(f"/?backend={backend.slug}")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200, response.data
    assert len(response.data["results"]) == 1


def test_jobrequestapilist_filter_by_backend_with_mismatched(api_rf, mocker):
    backend1 = BackendFactory()
    JobRequestFactory(backend=backend1)

    backend2 = BackendFactory()
    job_request = JobRequestFactory(backend=backend2)

    mocked_sentry = mocker.patch("jobserver.api.jobs.sentry_sdk", autospec=True)

    request = api_rf.get(
        f"/?backend={backend2.slug}", HTTP_AUTHORIZATION=backend1.auth_token
    )
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200, response.data
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["identifier"] == job_request.identifier

    assert mocked_sentry.capture_message.call_count == 1


def test_jobrequestapilist_filter_by_databricks(api_rf):
    job_request = JobRequestFactory(backend=BackendFactory(slug="databricks"))
    JobRequestFactory(backend=BackendFactory())

    request = api_rf.get("/?backend=nhsd")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200, response.data
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["identifier"] == job_request.identifier


def test_jobrequestapilist_get_only(api_rf):
    request = api_rf.post("/", data={}, format="json")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 405


def test_jobrequestapilist_produce_stats_when_authed(api_rf):
    backend = BackendFactory()

    assert Stats.objects.filter(backend=backend).count() == 0

    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200
    assert Stats.objects.filter(backend=backend).count() == 1


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


def test_userapidetail_success(api_rf):
    backend = BackendFactory()
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    response = UserAPIDetail.as_view()(request, username=user.username)

    assert response.status_code == 200

    # permissions
    permissions = response.data["permissions"]
    assert permissions["global"] == [
        "application_manage",
        "backend_manage",
        "org_create",
        "user_manage",
    ]
    assert permissions["orgs"] == [
        # we have no permissions for OrgCoordinator yet
        {
            "slug": org.slug,
            "permissions": [],
        },
    ]
    assert permissions["projects"] == [
        {
            "slug": project.slug,
            "permissions": [
                "job_cancel",
                "job_run",
                "snapshot_create",
                "workspace_archive",
                "workspace_create",
                "workspace_toggle_notifications",
            ],
        }
    ]

    # roles
    roles = response.data["roles"]
    assert roles["global"] == ["CoreDeveloper"]
    assert roles["orgs"] == [{"slug": org.slug, "roles": ["OrgCoordinator"]}]
    assert roles["projects"] == [{"slug": project.slug, "roles": ["ProjectDeveloper"]}]


def test_userapidetail_unknown_user(api_rf):
    backend = BackendFactory()

    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    response = UserAPIDetail.as_view()(request, username="dummy-user")

    assert response.status_code == 404


def test_workspacestatusesapi_success(api_rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request, action="run_all", status="failed")

    request = api_rf.get("/")
    response = WorkspaceStatusesAPI.as_view()(request, name=workspace.name)

    assert response.status_code == 200
    assert response.data["run_all"] == "failed"


def test_workspacestatusesapi_unknown_workspace(api_rf):
    request = api_rf.get("/")
    response = WorkspaceStatusesAPI.as_view()(request, name="test")
    assert response.status_code == 404
