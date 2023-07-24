from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from ....factories import JobFactory, JobRequestFactory
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


def test_job_run_command_empty_project_definition():
    job_request = JobRequestFactory(project_definition="")

    assert JobFactory(job_request=job_request).run_command is None


def test_job_run_command_error_action():
    pipeline = """
    version: 3.0
    expectations:
      population_size: 1000
    actions:
      my_action:
        run: cowsay research!
        outputs:
          moderately_sensitive:
            log: logs/cowsay.log
    """

    job_request = JobRequestFactory(project_definition=pipeline)

    assert JobFactory(job_request=job_request, action="__error__").run_command is None


def test_job_run_command_invalid_project_definition():
    """
    Test an invalid project definition
    """
    pipeline = """
    version: 3.0
    expectations:
      population_size: 1000
    actions:
      my_action:
        run: cowsay research!
        outputs:
          moderately_sensitive:
            log: logs/cowsay.log
      another_action:
        needs: [my_action]
        run: cowsay research!
        outputs:
          moderately_sensitive:
            log: logs/cowsay.log
    """

    job_request = JobRequestFactory(project_definition=pipeline)

    assert JobFactory(job_request=job_request).run_command is None


def test_job_run_command_invalid_project_definition_yaml():
    """
    Test an invalid project definition
    """
    pipeline = """
    version: 3.0
    expectations:
      population_size: 1000
    actions:
      my_action:
        run: cowsay research!
      my_action:
        run: cowsay research!
    """

    job_request = JobRequestFactory(project_definition=pipeline)

    assert JobFactory(job_request=job_request).run_command is None


def test_job_run_command_success():
    pipeline = """
    version: 3.0
    expectations:
      population_size: 1000
    actions:
      my_action:
        run: cowsay research!
        outputs:
          moderately_sensitive:
            log: logs/cowsay.log
    """

    job_request = JobRequestFactory(project_definition=pipeline)
    job = JobFactory(job_request=job_request, action="my_action")

    assert job.run_command == "cowsay research!"


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
