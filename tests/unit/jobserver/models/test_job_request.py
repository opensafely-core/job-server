from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobserver.models import JobRequest

from ....factories import JobFactory, JobRequestFactory, RepoFactory, WorkspaceFactory
from ....utils import minutes_ago, seconds_ago


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
            "org_slug": job_request.workspace.project.org.slug,
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
            "org_slug": job_request.workspace.project.org.slug,
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


def test_jobrequest_is_completed():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, status="failed")
    JobFactory(job_request=job_request, status="succeeded")

    jr = JobRequest.objects.get(pk=job_request.pk)
    assert jr.is_completed


def test_jobrequest_is_invalid():
    job_request = JobRequestFactory()
    JobFactory(job_request=job_request, action="__error__")

    assert job_request.is_invalid


def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


def test_job_request_num_completed_success():
    job_request = JobRequestFactory()

    job1, job2 = JobFactory.create_batch(2, job_request=job_request, status="succeeded")

    assert job_request.num_completed == 2


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

    jr = JobRequest.objects.get(pk=job_request.pk)
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

    jr = JobRequest.objects.get(pk=job_request.pk)
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
    assert not JobRequest.objects.first().runtime


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

    job_request = JobRequest.objects.first()
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

    assert not JobRequest.objects.first().runtime


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

    job_request = JobRequest.objects.first()
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
        [jr.status for jr in JobRequest.objects.all()]


def test_jobrequest_status_without_prefetching_jobs(django_assert_num_queries):
    job_request = JobRequestFactory()
    JobFactory.create_batch(5, job_request=job_request)

    with pytest.raises(Exception, match="JobRequest queries must prefetch jobs."):
        job_request.status
