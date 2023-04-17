import json
from collections import OrderedDict

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
    AnalysisRequestFactory,
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
from tests.fakes import FakeGitHubAPI
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
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

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
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 3


def test_jobapiupdate_invalid_payload(api_rf):
    backend = BackendFactory()

    assert Job.objects.count() == 0

    data = [{"action": "test-action"}]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    assert Job.objects.count() == 0

    assert response.status_code == 400, response.data

    errors = response.data[0]
    assert len(errors.keys()) == 9


def test_jobapiupdate_is_behind_auth(api_rf):
    request = api_rf.post("/")
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

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
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

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


def test_jobapiupdate_notifications_on_with_move_to_succeeded(api_rf, mocker):
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

    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    mocked_send.assert_called_once()
    assert response.status_code == 200


def test_jobapiupdate_notifications_on_without_move_to_completed(api_rf, mocker):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace, will_notify=True)
    job = JobFactory(job_request=job_request, status="succeeded")

    now = timezone.now()

    mocked_send_finished = mocker.patch(
        "jobserver.api.jobs.send_finished_notification", autospec=True
    )
    mocked_notify_output_checkers = mocker.patch(
        "jobserver.api.jobs.notify_output_checkers", autospec=True
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

    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    mocked_send_finished.assert_not_called()
    mocked_notify_output_checkers.assert_not_called()
    assert response.status_code == 200


def test_jobapiupdate_post_job_request_error(api_rf):
    backend = BackendFactory()
    job_request = JobRequestFactory(will_notify=True)

    now = timezone.now().isoformat()

    assert Job.objects.count() == 0

    data = [
        {
            "identifier": "job1",
            "job_request_id": job_request.identifier,
            "action": "__error__",
            "status": "failed",
            "status_code": "",
            "status_message": "",
            "created_at": now,
            "started_at": now,
            "updated_at": now,
            "completed_at": now,
        },
    ]

    request = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 1


def test_jobapiupdate_post_only(api_rf):
    backend = BackendFactory()

    # GET
    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert (
        JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request).status_code == 405
    )

    # HEAD
    request = api_rf.head("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert (
        JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request).status_code == 405
    )

    # PATCH
    request = api_rf.patch("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert (
        JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request).status_code == 405
    )

    # PUT
    request = api_rf.put("/", HTTP_AUTHORIZATION=backend.auth_token)
    assert (
        JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request).status_code == 405
    )


@pytest.mark.parametrize(
    "error_message",
    [
        "Internal error",
        "Something went wrong with the database, please contact tech support",
        "Ran out of memory (limit for this job was 6GB)",
    ],
)
def test_jobapiupdate_post_with_errors(api_rf, mocker, error_message):
    backend = BackendFactory()
    job_request = JobRequestFactory()
    mocked_sentry = mocker.patch("jobserver.api.jobs.sentry_sdk", autospec=True)

    now = timezone.now()

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
    JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request_1)

    data[0]["status"] = "failed"
    data[0]["status_message"] = error_message
    request_2 = api_rf.post(
        "/", HTTP_AUTHORIZATION=backend.auth_token, data=data, format="json"
    )
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request_2)

    assert response.status_code == 200, response.data

    mocked_sentry.capture_message.assert_called_once()


def test_jobapiupdate_post_with_flags(api_rf):
    backend = BackendFactory()
    job_request = JobRequestFactory()

    now = timezone.now()

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
        }
    ]

    flags = json.dumps(
        {
            "mode": {"v": "test", "ts": "1659092411.5025"},
            "paused": {"v": " ", "ts": "1657099752.16788"},
            "db-maintenance": {"v": "", "ts": "1657194377.72893"},
        },
        separators=(",", ":"),
    )

    request = api_rf.post(
        "/",
        data=data,
        format="json",
        HTTP_AUTHORIZATION=backend.auth_token,
        HTTP_FLAGS=flags,
    )
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200, response.data
    assert Job.objects.count() == 1

    backend.refresh_from_db()
    assert backend.jobrunner_state["mode"]["v"] == "test"


def test_jobapiupdate_post_with_failed_job_request_from_interactive(
    api_rf, slack_messages
):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    AnalysisRequestFactory(job_request=job_request)
    job = JobFactory(job_request=job_request, status="running")

    now = timezone.now()

    data = [
        {
            "identifier": job.identifier,
            "job_request_id": job_request.identifier,
            "action": "test",
            "status": "failed",
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

    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]

    assert channel == "tech-support-channel"
    assert job_request.get_absolute_url() in text


def test_jobapiupdate_post_with_successful_job_request_from_interactive(api_rf, mocker):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    job = JobFactory(job_request=job_request, status="running")
    AnalysisRequestFactory(job_request=job_request)

    # build a mock of the GitHubAPI so we can test that it was invoked as
    # expected
    mocked_api = mocker.patch("jobserver.github.GitHubAPI", autospec=True)()

    now = timezone.now()

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

    response = JobAPIUpdate.as_view(get_github_api=lambda: mocked_api)(request)

    assert response.status_code == 200
    mocked_api.create_issue.assert_called_once()


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
    response = JobAPIUpdate.as_view(get_github_api=FakeGitHubAPI)(request)

    # Jobs associated with unknown requests should be ignored
    assert response.status_code == 200, response.data
    assert not Job.objects.exists()


def test_jobrequestapilist_filter_by_backend(api_rf):
    backend = BackendFactory()
    JobRequestFactory(backend=backend)
    JobRequestFactory()

    request = api_rf.get("/", HTTP_AUTHORIZATION=backend.auth_token)
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200, response.data
    assert len(response.data["results"]) == 1


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
    now = timezone.now()

    # Python's datetime.isoformat does not support military timezones, so to
    # get the UTC suffix of "Z" we're using this function to wrap strftime.
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project, created_at=now)

    # all completed
    backend1 = BackendFactory(slug="test-1")
    job_request1 = JobRequestFactory(
        backend=backend1, workspace=workspace, created_at=now, identifier="jr1"
    )
    JobFactory.create_batch(2, job_request=job_request1, completed_at=now)

    # some completed
    backend2 = BackendFactory(slug="test-2")
    job_request2 = JobRequestFactory(
        backend=backend2,
        workspace=workspace,
        created_at=now,
        identifier="jr2",
        requested_actions=["frob", "wizzle"],
    )
    JobFactory(job_request=job_request2, completed_at=now, action="frob")
    JobFactory(job_request=job_request2, completed_at=None, action="wizzle")

    # none completed
    job_request3 = JobRequestFactory(
        backend=backend2,
        workspace=workspace,
        created_at=now,
        identifier="jr3",
        requested_actions=["frobnicate", "wibble"],
    )
    JobFactory(job_request=job_request3, completed_at=None, action="frobnicate")
    JobFactory(job_request=job_request3, completed_at=None, action="wibble")

    #  no jobs
    backend3 = BackendFactory(slug="test-3")
    job_request4 = JobRequestFactory(
        backend=backend3,
        workspace=workspace,
        created_at=now,
        identifier="jr4",
        requested_actions=["analyse"],
    )

    assert JobRequest.objects.count() == 4

    request = api_rf.get("/")
    response = JobRequestAPIList.as_view()(request)

    assert response.status_code == 200

    def dictify(od):
        """Recursively convert OrderedDicts to dicts"""
        return {
            k: dictify(v) if isinstance(v, OrderedDict) else v for k, v in od.items()
        }

    results = [dictify(r) for r in response.data["results"]]

    # sort results based on the manually set identifiers because we don't care
    # about ordering here
    results = list(sorted(results, key=lambda r: r["identifier"]))

    assert results == [
        {
            "backend": "test-2",
            "cancelled_actions": [],
            "created_at": now_iso,
            "created_by": job_request2.created_by.username,
            "force_run_dependencies": False,
            "identifier": job_request2.identifier,
            "orgs": [project.org.slug],
            "project": project.slug,
            "requested_actions": ["frob", "wizzle"],
            "sha": "",
            "workspace": {
                "name": workspace.name,
                "repo": workspace.repo.url,
                "branch": "",
                "db": "full",
                "created_by": workspace.created_by.username,
                "created_at": now_iso,
            },
        },
        {
            "backend": "test-2",
            "cancelled_actions": [],
            "created_at": now_iso,
            "created_by": job_request3.created_by.username,
            "force_run_dependencies": False,
            "identifier": job_request3.identifier,
            "orgs": [project.org.slug],
            "project": project.slug,
            "requested_actions": ["frobnicate", "wibble"],
            "sha": "",
            "workspace": {
                "name": workspace.name,
                "repo": workspace.repo.url,
                "branch": "",
                "db": "full",
                "created_by": workspace.created_by.username,
                "created_at": now_iso,
            },
        },
        {
            "backend": "test-3",
            "cancelled_actions": [],
            "created_at": now_iso,
            "created_by": job_request4.created_by.username,
            "force_run_dependencies": False,
            "identifier": job_request4.identifier,
            "orgs": [project.org.slug],
            "project": project.slug,
            "requested_actions": ["analyse"],
            "sha": "",
            "workspace": {
                "name": workspace.name,
                "repo": workspace.repo.url,
                "branch": "",
                "db": "full",
                "created_by": workspace.created_by.username,
                "created_at": now_iso,
            },
        },
    ]


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
                "unreleased_outputs_view",
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
