from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from jobserver.models import Job

from ....factories import (
    BackendFactory,
    JobFactory,
    JobRequestFactory,
    WorkspaceFactory,
)
from ....utils import minutes_ago


def test_job_get_absolute_url():
    job = JobFactory()

    url = job.get_absolute_url()

    assert url == reverse(
        "job-detail",
        kwargs={
            "project_slug": job.job_request.workspace.project.slug,
            "workspace_slug": job.job_request.workspace.name,
            "pk": job.job_request.pk,
            "identifier": job.identifier,
        },
    )


def test_job_get_cancel_url():
    job = JobFactory()

    url = job.get_cancel_url()

    assert url == reverse(
        "job-cancel",
        kwargs={
            "project_slug": job.job_request.workspace.project.slug,
            "workspace_slug": job.job_request.workspace.name,
            "pk": job.job_request.pk,
            "identifier": job.identifier,
        },
    )


def test_job_get_redirect_url():
    job = JobFactory()

    url = job.get_redirect_url()

    assert url == reverse("job-redirect", kwargs={"identifier": job.identifier})


def test_job_is_missing_updates_above_threshold():
    last_update = minutes_ago(timezone.now(), 50)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert job.is_missing_updates


def test_job_is_missing_updates_below_threshold():
    last_update = minutes_ago(timezone.now(), 29)
    job = JobFactory(completed_at=None, updated_at=last_update)

    assert not job.is_missing_updates


def test_job_is_missing_updates_missing_updated_at():
    assert not JobFactory(status="pending", updated_at=None).is_missing_updates


def test_job_is_missing_updates_completed():
    assert not JobFactory(status="failed").is_missing_updates


def test_jobrequest_previous_exists():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    job_request_1 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request_2 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request_3 = JobRequestFactory(workspace=workspace, backend=backend)

    first_job = JobFactory(job_request=job_request_1, action="test")
    second_job = JobFactory(job_request=job_request_2, action="test")
    JobFactory(job_request=job_request_3, action="test")

    assert Job.objects.previous(second_job) == first_job


def test_jobrequest_previous_does_not_exist():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    job_request = JobRequestFactory(workspace=workspace, backend=backend)

    job = JobFactory(job_request=job_request, action="test")

    assert Job.objects.previous(job) is None


def test_jobrequest_previous_different_action_does_not_exist():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    first_job_request = JobRequestFactory(workspace=workspace, backend=backend)
    second_job_request = JobRequestFactory(workspace=workspace, backend=backend)

    first_job = JobFactory(job_request=first_job_request, action="test")
    second_job = JobFactory(job_request=second_job_request, action="test123")

    assert Job.objects.previous(second_job) != first_job


def test_jobrequest_previous_suceeded():
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    job_request_1 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request_2 = JobRequestFactory(workspace=workspace, backend=backend)
    job_request_3 = JobRequestFactory(workspace=workspace, backend=backend)

    job_1 = JobFactory(job_request=job_request_1, action="test", status="succeeded")
    JobFactory(job_request=job_request_2, action="test", status="failed")
    job_3 = JobFactory(job_request=job_request_3, action="test")

    assert Job.objects.previous(job_3, succeeded=True) == job_1


def test_job_runtime():
    duration = timedelta(hours=1, minutes=2, seconds=3)
    started_at = timezone.now() - duration
    job = JobFactory(
        status="succeeded", started_at=started_at, completed_at=timezone.now()
    )

    assert job.runtime.hours == 1
    assert job.runtime.minutes == 2
    assert job.runtime.seconds == 3


def test_job_runtime_not_completed():
    job = JobFactory(status="running", started_at=timezone.now())

    # an uncompleted job has no runtime
    assert not job.runtime


def test_job_runtime_not_started():
    job = JobFactory(status="pending")

    # an unstarted job has no runtime
    assert not job.runtime


def test_job_runtime_without_timestamps():
    job = JobFactory(status="succeeded", started_at=None, completed_at=None)

    assert not job.runtime


def test_job_str():
    job = JobFactory(action="Run")

    assert str(job) == f"Run ({job.pk})"
