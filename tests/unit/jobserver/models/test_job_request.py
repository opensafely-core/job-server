from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import JobRequest

from ....factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    RepoFactory,
    WorkspaceFactory,
)
from ....utils import minutes_ago, seconds_ago


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_jobrequest_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        JobRequestFactory(**{field: None})


def test_jobrequest_completed_at_no_jobs():
    assert not JobRequestFactory().completed_at


def test_jobrequest_completed_at_success():
    test_completed_at = timezone.now()

    job_request = JobRequestFactory()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        completed_at=(test_completed_at - timedelta(minutes=1)),
    )
    job2 = JobFactory(
        job_request=job_request, status="succeeded", completed_at=test_completed_at
    )

    jr = JobRequest.objects.get(pk=job_request.pk)

    assert jr.completed_at == test_completed_at
    assert jr.completed_at == job2.completed_at


def test_jobrequest_completed_at_while_incomplete():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request, completed_at=timezone.now())
    JobFactory(job_request=job_request)

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert not jr.completed_at


def test_jobrequest_get_absolute_url():
    job_request = JobRequestFactory()

    url = job_request.get_absolute_url()

    assert url == reverse(
        "job-request-detail",
        kwargs={
            "project_slug": job_request.workspace.project.slug,
            "workspace_slug": job_request.workspace.name,
            "pk": job_request.pk,
        },
    )


def test_jobrequest_get_cancel_url():
    job_request = JobRequestFactory()

    url = job_request.get_cancel_url()

    assert url == reverse(
        "job-request-cancel",
        kwargs={
            "project_slug": job_request.workspace.project.slug,
            "workspace_slug": job_request.workspace.name,
            "pk": job_request.pk,
        },
    )


def test_jobrequest_get_project_yaml_url_no_sha():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo"


def test_jobrequest_get_project_yaml_url_success():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_file_url("test-blah.foo")

    assert url == "http://example.com/opensafely/some_repo/blob/abc123/test-blah.foo"


def test_jobrequest_get_repo_url_no_sha():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo"


def test_jobrequest_get_repo_url_success():
    repo = RepoFactory(url="http://example.com/opensafely/some_repo")
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace, sha="abc123")

    url = job_request.get_repo_url()

    assert url == "http://example.com/opensafely/some_repo/tree/abc123"


def test_jobrequest_get_staff_url():
    job_request = JobRequestFactory()

    url = job_request.get_staff_url()

    assert url == reverse(
        "staff:job-request-detail",
        kwargs={
            "pk": job_request.pk,
        },
    )


def test_jobrequest_get_staff_cancel_url():
    job_request = JobRequestFactory()

    url = job_request.get_staff_cancel_url()

    assert url == reverse(
        "staff:job-request-cancel",
        kwargs={
            "pk": job_request.pk,
        },
    )


def test_jobrequest_is_completed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.is_completed


def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


def test_jobrequest_num_completed_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.num_completed == 2


def test_jobrequest_previous_exists():
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    a, b, _ = JobRequestFactory.create_batch(3, workspace=workspace, backend=backend)
    previous = JobRequest.objects.previous(b)
    assert previous == a


def test_jobrequest_previous_nonexistent():
    job_request = JobRequestFactory()
    previous = JobRequest.objects.previous(job_request)
    assert previous is None


def test_jobrequest_previous_succeeded():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    job_request1 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request1.jobs.add(JobFactory(status="succeeded"))
    job_request1.jobs.add(JobFactory(status="succeeded"))

    job_request2 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request2.jobs.add(JobFactory(status="succeeded"))
    job_request2.jobs.add(JobFactory(status="failed"))
    job_request2.jobs.add(JobFactory(status="zzzinvalidstatus"))

    job_request3 = JobRequestFactory(workspace=workspace, backend=backend)

    previous = JobRequest.objects.previous(job_request3, filter_succeeded=True)
    assert previous == job_request1


def test_jobrequest_previous_url():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    a = JobRequestFactory(workspace=workspace, backend=backend, sha="abc1234")
    b = JobRequestFactory(workspace=workspace, backend=backend, sha="def5678")
    comp_url = workspace.repo.get_compare_url(b.sha, a.sha)
    assert comp_url.endswith("def5678..abc1234")


def test_jobrequest_request_cancellation():
    job_request = JobRequestFactory(cancelled_actions=[])
    JobFactory(job_request=job_request, action="job1", status="pending")
    JobFactory(job_request=job_request, action="job2", status="running")
    JobFactory(job_request=job_request, action="job3", status="failed")
    JobFactory(job_request=job_request, action="job4", status="succeeded")

    job_request.request_cancellation()

    job_request.refresh_from_db()
    assert set(job_request.cancelled_actions) == {"job1", "job2"}


def test_jobrequest_runtime_one_job_missing_completed_at(freezer):
    job_request = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=job_request,
        status="succeeded",
        started_at=minutes_ago(now, 3),
        completed_at=minutes_ago(now, 2),
    )
    JobFactory(
        job_request=job_request,
        status="running",
        started_at=minutes_ago(now, 1),
        completed_at=None,
    )

    jr = JobRequest.objects.with_started_at().get(pk=job_request.pk)
    assert jr.started_at
    assert not jr.completed_at

    # combined _completed_ Job runtime is 0 because the failed job has no
    # runtime (it never started)
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 1
    assert jr.runtime.seconds == 0


def test_jobrequest_runtime_one_job_missing_started_at(freezer):
    job_request = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=minutes_ago(now, 5),
        completed_at=minutes_ago(now, 3),
    )
    JobFactory(
        job_request=job_request,
        status="failed",
        started_at=None,
        completed_at=timezone.now(),
    )

    jr = JobRequest.objects.with_started_at().get(pk=job_request.pk)
    assert jr.started_at
    assert jr.completed_at

    # combined _completed_ Job runtime is 2 minutes because the second job
    # failed before it started
    assert jr.runtime
    assert jr.runtime.hours == 0
    assert jr.runtime.minutes == 2
    assert jr.runtime.seconds == 0


def test_jobrequest_runtime_no_jobs():
    JobRequestFactory()
    assert not JobRequest.objects.with_started_at().first().runtime


def test_jobrequest_runtime_not_completed(freezer):
    jr = JobRequestFactory()

    now = timezone.now()

    JobFactory(
        job_request=jr,
        status="succeeded",
        started_at=minutes_ago(now, 2),
        completed_at=minutes_ago(now, 1),
    )
    JobFactory(
        job_request=jr,
        status="running",
        started_at=seconds_ago(now, 30),
    )

    job_request = JobRequest.objects.with_started_at().first()
    assert job_request.started_at
    assert not job_request.completed_at

    # combined _completed_ Job runtime is 1 minute
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 1
    assert job_request.runtime.seconds == 0


def test_jobrequest_runtime_not_started():
    jr = JobRequestFactory()

    JobFactory(job_request=jr, status="running")
    JobFactory(job_request=jr, status="pending")

    assert not JobRequest.objects.with_started_at().first().runtime


def test_jobrequest_runtime_success():
    jr = JobRequestFactory()

    start = timezone.now() - timedelta(hours=1)

    JobFactory(
        job_request=jr,
        status="succeeded",
        started_at=start,
        completed_at=start + timedelta(minutes=1),
    )
    JobFactory(
        job_request=jr,
        status="failed",
        started_at=start + timedelta(minutes=2),
        completed_at=start + timedelta(minutes=3),
    )

    job_request = JobRequest.objects.with_started_at().first()
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 2
    assert job_request.runtime.seconds == 0


@pytest.mark.parametrize(
    "statuses,expected",
    [
        (["failed", "failed", "failed", "failed"], "failed"),
        (["pending", "pending", "pending", "pending"], "pending"),
        (["running", "running", "running", "running"], "running"),
        (["succeeded", "succeeded", "succeeded", "succeeded"], "succeeded"),
    ],
)
def test_jobrequest_status_all_jobs_the_same(statuses, expected):
    job_request = JobRequestFactory()
    for status in statuses:
        JobFactory(job_request=job_request, status=status)

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == expected


def test_jobrequest_status_running_in_job_statuses():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="running")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "running"


def test_jobrequest_status_running_not_in_job_statues():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="pending")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "running"


def test_jobrequest_status_failed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "failed"


def test_jobrequest_status_unknown():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="foo")
    JobFactory(job_request=job_request, status="bar")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.status == "unknown"


def test_jobrequest_status_uses_prefetch_cache(django_assert_num_queries):
    for i in range(5):
        jr = JobRequestFactory()
        JobFactory.create_batch(5, job_request=jr)

    with django_assert_num_queries(2):
        # 1. select JobRequests
        # 2. select Jobs for those JobRequests
        [jr.status for jr in JobRequest.objects.with_started_at().all()]


def test_jobrequest_status_without_prefetching_jobs(django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory.create_batch(5, job_request=job_request)

    assert not hasattr(job_request, "_prefetched_objects_cache")

    job_request.status

    assert "jobs" in job_request._prefetched_objects_cache


def test_jobrequest_str():
    job_request = JobRequestFactory()

    assert str(job_request) == str(job_request.pk)


def test_jobrequestmanager_with_started_at():
    JobRequestFactory.create_batch(5)

    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)
    JobRequestFactory(workspace=workspace)

    assert JobRequest.objects.with_started_at().filter(workspace=workspace).count() == 2


def test_jobrequest_database_name_with_no_project_number(build_job_request):
    job_request = build_job_request(project_number=None)
    assert job_request.database_name == "default"


def test_jobrequest_database_name_without_t1oo_permission(build_job_request):
    job_request = build_job_request(project_number=1)
    assert job_request.database_name == "default"


def test_jobrequest_database_name_with_t1oo_permission(build_job_request):
    # This is one of the project numbers hardcoded into `permissions/t1oo.py`
    job_request = build_job_request(project_number=2)
    assert job_request.database_name == "include_t1oo"


@pytest.fixture
def build_job_request():
    def _build_job_request(project_number):
        project = ProjectFactory(number=project_number)
        workspace = WorkspaceFactory(project=project)
        return JobRequestFactory(workspace=workspace)

    return _build_job_request
