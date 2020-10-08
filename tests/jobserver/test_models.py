from datetime import timedelta

import pytest
import responses
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Job

from ..factories import JobFactory, JobRequestFactory, WorkspaceFactory


@pytest.mark.django_db
def test_job_get_absolute_url():
    job = JobFactory()

    url = job.get_absolute_url()

    assert url == reverse("job-detail", kwargs={"pk": job.pk})


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_action_failed():
    responses.add(responses.POST, "http://example.com", status=201)

    request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(
        request=request,
        action_id="Research",
        completed_at=timezone.now(),
        started=True,
        status_code=1,
        status_message="test",
    )

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.body
        == b'{"message": "Error in Research (status test)"}'
    )


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_action_finished():
    responses.add(responses.POST, "http://example.com", status=201)

    request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(
        request=request,
        action_id="Research",
        completed_at=timezone.now(),
        started=True,
        status_code=0,
        status_message="test",
    )

    assert len(responses.calls) == 1
    assert responses.calls[0].request.body == b'{"message": "Research finished: test"}'


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_starting_dependency():
    responses.add(responses.POST, "http://example.com", status=201)

    parent = JobFactory()

    request = JobRequestFactory(callback_url="http://example.com")
    job = JobFactory(
        request=request,
        action_id="Research",
        needed_by=parent,
        started=False,
    )

    assert len(responses.calls) == 1

    expected = f'{{"message": "Starting dependency Research, job#{job.pk}"}}'.encode()
    assert responses.calls[0].request.body == expected


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_started_with_no_parent():
    responses.add(responses.POST, "http://example.com", status=201)

    request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(request=request, started=False)

    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_with_no_callback_url():
    responses.add(responses.POST, "http://example.com", status=201)

    request = JobRequestFactory()
    JobFactory(request=request)

    assert len(responses.calls) == 0


@pytest.mark.django_db
def test_job_runtime():
    duration = timedelta(hours=1, minutes=2, seconds=3)
    started_at = timezone.now() - duration
    job = JobFactory(started_at=started_at, completed_at=timezone.now())

    assert job.runtime.hours == 1
    assert job.runtime.minutes == 2
    assert job.runtime.seconds == 3


@pytest.mark.django_db
def test_job_runtime_not_completed():
    job = JobFactory(started_at=timezone.now())

    # an unfinished job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_runtime_not_started():
    job = JobFactory()

    # an unstarted job has no runtime
    assert job.runtime is None


@pytest.mark.django_db
def test_job_save(freezer):
    job = JobFactory()

    assert job.started_at is None
    assert job.completed_at is None

    job.started = True
    job.status_code = 1
    job.save()

    assert job.started_at == timezone.now()
    assert job.completed_at == timezone.now()


@pytest.mark.django_db
def test_job_str():
    job = JobFactory(action_id="Run")

    assert str(job) == f"Run ({job.pk})"


@pytest.mark.django_db
def test_job_status_completed():
    now = timezone.now()
    one_minute = timedelta(seconds=60)
    job = JobFactory(started_at=now - one_minute, completed_at=now)

    assert job.status == "Completed"


@pytest.mark.django_db
def test_job_status_dependency_failed():
    job = JobFactory(status_code=7)

    assert job.status == "Dependency Failed"


@pytest.mark.django_db
def test_job_status_failed():
    job = JobFactory(status_code=1)

    assert job.status == "Failed"


@pytest.mark.django_db
def test_job_status_in_progress():
    one_minute = timedelta(seconds=60)
    job = JobFactory(started_at=timezone.now() - one_minute)

    assert job.status == "In Progress"


@pytest.mark.django_db
def test_job_status_status_6_is_pending():
    job = JobFactory(status_code=6)

    assert job.status == "Pending"


@pytest.mark.django_db
def test_job_status_unstarted_is_pending():
    job = JobFactory()
    assert job.status == "Pending"


@pytest.mark.django_db
def test_jobqueryset():
    JobFactory()
    JobFactory(started_at=timezone.now())
    JobFactory(completed_at=timezone.now())

    assert Job.objects.completed().count() == 1
    assert Job.objects.in_progress().count() == 1
    assert Job.objects.pending().count() == 1


@pytest.mark.django_db
def test_workspace_str():
    workspace = WorkspaceFactory(
        name="Corellian Engineering Corporation", repo="Corellia"
    )

    assert str(workspace) == "Corellian Engineering Corporation (Corellia)"


@pytest.mark.django_db
def test_workspace_get_absolute_url():
    workspace = WorkspaceFactory()
    url = workspace.get_absolute_url()
    assert url == reverse("workspace-detail", kwargs={"pk": workspace.pk})
