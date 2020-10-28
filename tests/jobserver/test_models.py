from datetime import timedelta

import pytest
import responses
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Job

from ..factories import JobFactory, JobRequestFactory, UserFactory, WorkspaceFactory


@pytest.mark.django_db
def test_job_get_absolute_url():
    job = JobFactory()

    url = job.get_absolute_url()

    assert url == reverse("job-detail", kwargs={"pk": job.pk})


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_action_failed():
    responses.add(responses.POST, "http://example.com", status=201)

    job_request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(
        job_request=job_request,
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

    job_request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(
        job_request=job_request,
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

    job_request = JobRequestFactory(callback_url="http://example.com")
    job = JobFactory(
        job_request=job_request,
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

    job_request = JobRequestFactory(callback_url="http://example.com")
    JobFactory(job_request=job_request, started=False)

    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_job_notify_callback_url_with_no_callback_url():
    responses.add(responses.POST, "http://example.com", status=201)

    job_request = JobRequestFactory()
    JobFactory(job_request=job_request)

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
def test_job_save_with_started_at_set(freezer):
    job = JobFactory()

    assert job.started_at is None
    assert job.completed_at is None

    start = timezone.now() - timedelta(hours=1)

    job.started = True
    job.started_at = start
    job.status_code = 1
    job.save()

    assert job.started_at == start
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
def test_jobrequest_completed_at_no_jobs():
    assert not JobRequestFactory().completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, completed_at=timezone.now())

    job1.needed_by = job2
    job1.save()

    assert job_request.completed_at == job2.completed_at


@pytest.mark.django_db
def test_jobrequest_completed_at_while_incomplete():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request)

    job1.needed_by = job2
    job1.save()

    assert not job_request.completed_at


@pytest.mark.django_db
def test_jobrequest_is_complete_no_jobs():
    assert not JobRequestFactory().is_complete


@pytest.mark.django_db
def test_jobrequest_is_complete_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job3 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job4 = JobFactory(job_request=job_request, completed_at=timezone.now())

    # set up hierarchy
    job1.needed_by = job2
    job1.save()

    job2.needed_by = job4
    job2.save()

    job3.needed_by = job4
    job3.save()

    assert job_request.is_complete


@pytest.mark.django_db
def test_jobrequest_is_failed_jobs_still_running():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(
        job_request=job_request, completed_at=timezone.now(), status_code=3
    )
    job3 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job4 = JobFactory(job_request=job_request)

    # set up hierarchy
    job1.needed_by = job2
    job1.save()

    job2.needed_by = job4
    job2.save()

    job3.needed_by = job4
    job3.save()

    assert not job_request.is_failed


@pytest.mark.django_db
def test_jobrequest_is_failed_no_jobs():
    assert not JobRequestFactory().is_failed


@pytest.mark.django_db
def test_jobrequest_is_failed_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(
        job_request=job_request, completed_at=timezone.now(), status_code=3
    )
    job3 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job4 = JobFactory(job_request=job_request, completed_at=timezone.now())

    # set up hierarchy
    job1.needed_by = job2
    job1.save()

    job2.needed_by = job4
    job2.save()

    job3.needed_by = job4
    job3.save()

    assert job_request.is_failed


@pytest.mark.django_db
def test_jobrequest_is_pending_no_jobs():
    assert JobRequestFactory().is_pending


@pytest.mark.django_db
def test_jobrequest_is_pending_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request)
    job2 = JobFactory(job_request=job_request)
    job3 = JobFactory(job_request=job_request)
    job4 = JobFactory(job_request=job_request)

    # set up hierarchy
    job1.needed_by = job2
    job1.save()

    job2.needed_by = job4
    job2.save()

    job3.needed_by = job4
    job3.save()

    assert job_request.is_pending


@pytest.mark.django_db
def test_jobrequest_num_completed_no_jobs():
    assert JobRequestFactory().num_completed == 0


@pytest.mark.django_db
def test_job_request_num_completed_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, completed_at=timezone.now())

    job1.needed_by = job2
    job1.save()

    assert job_request.num_completed == 2


@pytest.mark.django_db
def test_jobrequest_runtime_no_jobs():
    assert not JobRequestFactory().runtime


@pytest.mark.django_db
def test_jobrequest_runtime_not_completed(freezer):
    job_request = JobRequestFactory()

    job1 = JobFactory(
        job_request=job_request,
        started_at=timezone.now() - timedelta(minutes=2),
        completed_at=timezone.now() - timedelta(minutes=1),
    )
    job2 = JobFactory(
        job_request=job_request,
        started_at=timezone.now() - timedelta(seconds=30),
    )

    job1.needed_by = job2
    job1.save()

    assert job_request.started_at
    assert not job_request.completed_at

    # first job started 2 minutes ago so we should have 00:02:00
    assert job_request.runtime
    assert job_request.runtime.hours == 0
    assert job_request.runtime.minutes == 2
    assert job_request.runtime.seconds == 0


@pytest.mark.django_db
def test_jobrequest_runtime_not_started():
    job_request = JobRequestFactory()

    JobFactory(job_request=job_request)
    JobFactory(job_request=job_request)

    assert not job_request.runtime


@pytest.mark.django_db
def test_jobrequest_runtime_success():
    job_request = JobRequestFactory()

    start = timezone.now() - timedelta(hours=1)

    job1 = JobFactory(
        job_request=job_request,
        started_at=start,
        completed_at=start + timedelta(minutes=1),
    )
    job2 = JobFactory(
        job_request=job_request,
        started_at=start + timedelta(minutes=2),
        completed_at=start + timedelta(minutes=3),
    )

    # set up hierarchy
    job1.needed_by = job2
    job1.save()

    assert job_request.runtime


@pytest.mark.django_db
def test_jobrequest_started_at_no_jobs():
    assert not JobRequestFactory().started_at


@pytest.mark.django_db
def test_job_request_started_at_success():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, started_at=timezone.now())
    job2 = JobFactory(job_request=job_request, started_at=timezone.now())

    job1.needed_by = job2
    job1.save()

    assert job_request.started_at


@pytest.mark.django_db
def test_jobrequest_status_completed():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, completed_at=timezone.now())

    job1.needed_by = job2
    job1.save()

    assert job_request.status == "Completed"


@pytest.mark.django_db
def test_jobrequest_status_fall_through():
    assert JobRequestFactory().status == "Pending"


@pytest.mark.django_db
def test_jobrequest_status_failed():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, status_code=3)

    job1.needed_by = job2
    job1.save()

    assert job_request.status == "Failed"


@pytest.mark.django_db
def test_jobrequest_status_in_progress():
    job_request = JobRequestFactory()

    job1 = JobFactory(job_request=job_request, completed_at=timezone.now())
    job2 = JobFactory(job_request=job_request, started_at=timezone.now())

    job1.needed_by = job2
    job1.save()

    assert job_request.status == "In Progress"


@pytest.mark.django_db
def test_jobrequest_status_pending():
    assert JobRequestFactory().status == "Pending"


@pytest.mark.django_db
def test_jobqueryset():
    JobFactory()
    JobFactory(started_at=timezone.now())
    JobFactory(completed_at=timezone.now())

    assert Job.objects.completed().count() == 1
    assert Job.objects.in_progress().count() == 1
    assert Job.objects.pending().count() == 1


@pytest.mark.django_db
def test_user_name_with_first_and_last_name():
    user = UserFactory(first_name="first", last_name="last")

    assert user.name == "first last"


@pytest.mark.django_db
def test_user_name_without_first_and_last_name():
    user = UserFactory()
    assert user.name == user.username


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


@pytest.mark.django_db
def test_workspace_repo_name_no_path():
    workspace = WorkspaceFactory(repo="http://example.com")

    with pytest.raises(Exception, match="not in expected format"):
        workspace.repo_name


@pytest.mark.django_db
def test_workspace_repo_name_success():
    workspace = WorkspaceFactory(repo="http://example.com/foo/test")
    assert workspace.repo_name == "test"
