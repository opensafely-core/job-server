from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Backend, JobRequest

from ..factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    StatsFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.mark.django_db
def test_backend_no_configured_backends(monkeypatch):
    monkeypatch.setenv("BACKENDS", "")

    # backends are created by migrations
    assert Backend.objects.count() == 3


@pytest.mark.django_db
def test_backend_one_configured_backend(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    # backends are created by migrations
    assert Backend.objects.count() == 1


@pytest.mark.django_db
def test_backend_get_absolute_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_absolute_url()

    assert url == reverse("backend-detail", kwargs={"pk": backend.pk})


@pytest.mark.django_db
def test_backend_get_rotate_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_rotate_url()

    assert url == reverse("backend-rotate-token", kwargs={"pk": backend.pk})


@pytest.mark.django_db
def test_backend_rotate_token():
    backend = BackendFactory(auth_token="test")
    assert backend.auth_token == "test"

    backend.rotate_token()
    assert backend.auth_token != "test"


@pytest.mark.django_db
def test_backend_str():
    backend = BackendFactory(name="Test Backend")

    assert str(backend) == "Test Backend"


@pytest.mark.django_db
def test_job_get_absolute_url():
    job = JobFactory()

    url = job.get_absolute_url()

    assert url == reverse("job-detail", kwargs={"identifier": job.identifier})


@pytest.mark.django_db
def test_job_get_zombify_url():
    job = JobFactory()

    url = job.get_zombify_url()

    assert url == reverse("job-zombify", kwargs={"identifier": job.identifier})


@pytest.mark.django_db
def test_job_is_missing_updates_above_threshold():
    last_update = timezone.now() - timedelta(minutes=50)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert job.is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_below_threshold():
    last_update = timezone.now() - timedelta(minutes=29)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert not job.is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_missing_updated_at():
    assert not JobFactory(status="pending", updated_at=None).is_missing_updates


@pytest.mark.django_db
def test_job_is_missing_updates_completed():
    assert not JobFactory(status="failed").is_missing_updates


@pytest.mark.django_db
def test_job_runtime():
    duration = timedelta(hours=1, minutes=2, seconds=3)
    started_at = timezone.now() - duration
    job = JobFactory(
        status="succeeded", started_at=started_at, completed_at=timezone.now()
    )

    assert job.runtime.hours == 1
    assert job.runtime.minutes == 2
    assert job.runtime.seconds == 3


@pytest.mark.django_db
def test_job_runtime_not_finished():
    job = JobFactory(status="running", started_at=timezone.now())

    # an unfinished job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_runtime_not_started():
    job = JobFactory(status="pending")

    # an unstarted job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_runtime_without_timestamps():
    job = JobFactory(status="succeeded", started_at=None, completed_at=None)

    assert job.runtime is None


@pytest.mark.django_db
def test_job_str():
    job = JobFactory(action="Run")

    assert str(job) == f"Run ({job.pk})"


@pytest.mark.django_db
def test_jobrequest_completed_at_no_jobs():
    assert not JobRequestFactory().completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.completed_at == job2.completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_while_incomplete():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, completed_at=timezone.now())
    JobFactory(job_request=job_request)

    assert not job_request.completed_at


@pytest.mark.django_db
def test_jobrequest_get_absolute_url():
    job_request = JobRequestFactory()
    url = job_request.get_absolute_url()
    assert url == reverse("job-request-detail", kwargs={"pk": job_request.pk})


@pytest.mark.django_db
def test_jobrequest_get_project_yaml_url_no_sha():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_project_yaml_url()

    assert url == "http://example.com/opensafely/some_repo"


@pytest.mark.django_db
def test_jobrequest_get_project_yaml_url_success():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_project_yaml_url()

    assert url == "http://example.com/opensafely/some_repo/blob/abc123/project.yaml"


@pytest.mark.django_db
def test_jobrequest_get_repo_url_no_sha():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo"


@pytest.mark.django_db
def test_jobrequest_get_repo_url_success():
    workspace = WorkspaceFactory(repo="http://example.com/opensafely/some_repo")
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo/tree/abc123"


@pytest.mark.django_db
def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


@pytest.mark.django_db
def test_job_request_num_completed_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.num_completed == 2


@pytest.mark.django_db
def test_jobrequest_runtime_no_jobs():
    assert not JobRequestFactory().runtime


@pytest.mark.django_db
def test_jobrequest_runtime_not_finished(freezer):
    job_request = JobRequestFactory()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=timezone.now() - timedelta(minutes=2),
        completed_at=timezone.now() - timedelta(minutes=1),
    )
    JobFactory(
        job_request=job_request,
        status="running",
        started_at=timezone.now() - timedelta(seconds=30),
    )

    assert job_request.started_at
    assert not job_request.completed_at

    # combined _finished_ Job runtime is 1 minute
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 1
    assert job_request.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_runtime_not_started():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="pending")

    assert not job_request.runtime


@pytest.mark.django_db
def test_jobrequest_runtime_success():
    job_request = JobRequestFactory()

    start = timezone.now() - timedelta(hours=1)

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=start,
        completed_at=start + timedelta(minutes=1),
    )
    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=start + timedelta(minutes=2),
        completed_at=start + timedelta(minutes=3),
    )

    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 2
    assert job_request.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_started_at_no_jobs():
    assert not JobRequestFactory().started_at


@pytest.mark.django_db
def test_jobrequest_started_at_success():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, started_at=timezone.now())
    JobFactory(job_request=job_request, started_at=timezone.now())

    assert job_request.started_at


@pytest.mark.django_db
def test_jobrequest_status_all_jobs_the_same(subtests):
    status_groups = [
        ["failed", "failed", "failed", "failed"],
        ["pending", "pending", "pending", "pending"],
        ["running", "running", "running", "running"],
        ["succeeded", "succeeded", "succeeded", "succeeded"],
    ]
    for statuses in status_groups:
        with subtests.test(statuses=statuses):
            job_request = JobRequestFactory()
            for status in statuses:
                JobFactory(job_request=job_request, status=status)

            assert job_request.status == statuses[0]


@pytest.mark.django_db
def test_jobrequest_status_running_in_job_statuses():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    assert job_request.status == "running"


@pytest.mark.django_db
def test_jobrequest_status_running_not_in_job_statues():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    assert job_request.status == "running"


@pytest.mark.django_db
def test_jobrequest_status_failed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    assert job_request.status == "failed"


@pytest.mark.django_db
def test_jobrequest_status_unknown():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="foo")
    JobFactory(job_request=job_request, status="bar")

    assert job_request.status == "unknown"


@pytest.mark.django_db
def test_jobrequestqueryset_acked():
    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(3)

    assert JobRequest.objects.acked().count() == 3


@pytest.mark.django_db
def test_jobrequestqueryset_unacked():
    JobRequestFactory.create_batch(3)

    assert JobRequest.objects.unacked().count() == 3


@pytest.mark.django_db
def test_stats_str_with_last_seen(freezer):
    tpp = Backend.objects.get(name="tpp")

    last_seen = datetime(2020, 12, 25, 10, 11, 12, tzinfo=timezone.utc)
    stats = StatsFactory(backend=tpp, api_last_seen=last_seen, url="/foo")

    assert str(stats) == "tpp | 2020-12-25 10:11:12 | /foo"


@pytest.mark.django_db
def test_stats_str_without_last_seen(freezer):
    tpp = Backend.objects.get(name="tpp")

    stats = StatsFactory(backend=tpp, api_last_seen=None, url="")

    assert str(stats) == "tpp | never | "


@pytest.mark.django_db
def test_user_name_with_first_and_last_name():
    user = UserFactory(first_name="first", last_name="last")

    assert user.name == "first last"


@pytest.mark.django_db
def test_user_name_without_first_and_last_name():
    user = UserFactory()
    assert user.name == user.username


@pytest.mark.django_db
def test_workspace_get_absolute_url():
    workspace = WorkspaceFactory()
    url = workspace.get_absolute_url()
    assert url == reverse("workspace-detail", kwargs={"name": workspace.name})


@pytest.mark.django_db
def test_workspace_get_archive_toggle_url():
    workspace = WorkspaceFactory()

    url = workspace.get_archive_toggle_url()

    assert url == reverse("workspace-archive-toggle", kwargs={"name": workspace.name})


@pytest.mark.django_db
def test_workspace_get_notifications_toggle_url():
    workspace = WorkspaceFactory()

    url = workspace.get_notifications_toggle_url()

    assert url == reverse(
        "workspace-notifications-toggle", kwargs={"name": workspace.name}
    )


@pytest.mark.django_db
def test_workspace_get_statuses_url():
    workspace = WorkspaceFactory()
    url = workspace.get_statuses_url()
    assert url == reverse("workspace-statuses", kwargs={"name": workspace.name})


@pytest.mark.django_db
def test_workspace_get_action_status_lut_no_jobs():
    assert WorkspaceFactory().get_action_status_lut() == {}


@pytest.mark.django_db
def test_workspace_get_action_status_lut_success():
    workspace1 = WorkspaceFactory()
    job_request1 = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request1, action="other-test", status="succeeded")

    workspace2 = WorkspaceFactory()
    job_request2 = JobRequestFactory(workspace=workspace2)

    JobFactory(
        job_request=job_request2,
        action="test",
        status="failed",
        created_at=timezone.now() - timedelta(minutes=3),
    )
    JobFactory(
        job_request=job_request2,
        action="test",
        status="failed",
        created_at=timezone.now() - timedelta(minutes=2),
    )
    JobFactory(
        job_request=job_request2,
        action="test",
        status="succeeded",
        created_at=timezone.now() - timedelta(minutes=1),
    )

    output = workspace2.get_action_status_lut()

    assert output == {"test": "succeeded"}


@pytest.mark.django_db
def test_workspace_repo_name_no_path():
    workspace = WorkspaceFactory(repo="http://example.com")

    with pytest.raises(Exception, match="not in expected format"):
        workspace.repo_name


@pytest.mark.django_db
def test_workspace_repo_name_success():
    workspace = WorkspaceFactory(repo="http://example.com/foo/test")
    assert workspace.repo_name == "test"


@pytest.mark.django_db
def test_workspace_str():
    workspace = WorkspaceFactory(
        name="Corellian Engineering Corporation", repo="Corellia"
    )
    assert str(workspace) == "Corellian Engineering Corporation (Corellia)"
