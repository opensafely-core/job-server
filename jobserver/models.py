import datetime

import pytz
import requests
import structlog
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from furl import furl

from .runtime import Runtime


logger = structlog.get_logger(__name__)


class Workspace(models.Model):
    created_by = models.ForeignKey("User", null=True, on_delete=models.CASCADE)

    name = models.TextField()
    repo = models.TextField(db_index=True)
    branch = models.TextField()

    DB_OPTIONS = (
        ("dummy", "Dummy database"),
        ("slice", "Cut-down (but real) database"),
        ("full", "Full database"),
    )
    db = models.TextField(choices=DB_OPTIONS)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.repo})"

    def get_absolute_url(self):
        return reverse("workspace-detail", kwargs={"pk": self.pk})

    def get_latest_status_for_action(self, action):
        """
        Get the latest status for an action in this Workspace
        """

        try:
            job = Job.objects.filter(
                action_id=action, job_request__workspace=self
            ).latest("created_at")
        except Job.DoesNotExist:
            return "-"

        return job.status

    @property
    def repo_name(self):
        """Convert repo URL -> repo name"""
        f = furl(self.repo)

        if not f.path:
            raise Exception("Repo URL not in expected format, appears to have no path")

        return f.path.segments[-1]


class JobQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(completed_at__isnull=False)

    def in_progress(self):
        return self.filter(started_at__isnull=False, completed_at=None)

    def pending(self):
        return self.filter(started_at=None, completed_at=None)


class Job(models.Model):
    force_run = models.BooleanField(default=False)
    started = models.BooleanField(default=False)
    action_id = models.TextField()
    status_code = models.IntegerField(null=True, blank=True)
    status_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    needed_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    job_request = models.ForeignKey(
        "JobRequest", null=True, on_delete=models.CASCADE, related_name="jobs"
    )
    workspace = models.ForeignKey(
        Workspace,
        related_name="jobs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.action_id} ({self.pk})"

    def get_absolute_url(self):
        return reverse("job-detail", kwargs={"pk": self.pk})

    @property
    def is_complete(self):
        return self.status_code is None and self.completed_at

    @property
    def is_dependency_failed(self):
        return self.status_code == 7

    @property
    def is_failed(self):
        dependency_not_finished = 6
        dependency_failed = 7
        dependency_running = 8

        non_failure_status = self.status_code in [
            dependency_not_finished,
            dependency_failed,
            dependency_running,
        ]

        return self.status_code and not non_failure_status

    @property
    def is_in_progress(self):
        if self.status_code is not None:
            return False

        return self.started_at and not self.completed_at

    @property
    def is_pending(self):
        if self.status_code in [6, 8]:
            return True

        if self.status_code is None and not (self.started_at and self.completed_at):
            return True

        return False

    def notify_callback_url(self):
        if not self.job_request.callback_url:
            return

        # A new dependency has been added; notify the originating thread
        if self.needed_by and not self.started:
            status = f"Starting dependency {self.action_id}, job#{self.pk}"
        elif self.started and self.completed_at:
            if self.status_code == 0:
                status = f"{self.action_id} finished: {self.status_message}"
            else:
                status = f"Error in {self.action_id} (status {self.status_message})"
        else:
            return

        requests.post(self.job_request.callback_url, json={"message": status})

    @property
    def runtime(self):
        if self.started_at is None:
            return

        if self.completed_at is None:
            return

        delta = self.completed_at - self.started_at

        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds))

    @property
    def status(self):
        if self.is_complete:
            return "Completed"

        if self.is_dependency_failed:
            return "Dependency Failed"

        if self.is_failed:
            return "Failed"

        if self.is_in_progress:
            return "In Progress"

        if self.is_pending:
            return "Pending"

        return "Pending"

    def save(self, *args, **kwargs):
        if self.started and not self.started_at:
            self.started_at = datetime.datetime.now(tz=pytz.UTC)

        if self.status_code is not None and not self.completed_at:
            if self.started:
                self.completed_at = datetime.datetime.now(tz=pytz.UTC)

        super().save(*args, **kwargs)

        self.notify_callback_url()


class JobOutput(models.Model):
    location = models.TextField()
    job = models.ForeignKey(
        Job, null=True, blank=True, related_name="outputs", on_delete=models.SET_NULL
    )


class JobRequest(models.Model):
    """
    A request to run a Job

    This represents the request, from a Human, to run a given Job in a
    Workspace.  The job-runner will create any required Jobs for the requested
    one to run.  All Jobs, either added by Human or Computer, are then grouped
    by this object.
    """

    EMIS = "emis"
    TPP = "tpp"
    BACKEND_CHOICES = [
        (EMIS, "EMIS"),
        (TPP, "TPP"),
    ]

    created_by = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    workspace = models.ForeignKey(
        "Workspace", on_delete=models.CASCADE, related_name="job_requests"
    )

    backend = models.TextField(choices=BACKEND_CHOICES, db_index=True)
    force_run = models.BooleanField(default=False)
    force_run_dependencies = models.BooleanField(default=False)
    requested_actions = models.JSONField()
    callback_url = models.TextField(null=True, blank=True)
    sha = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def completed_at(self):
        last_job = self.jobs.order_by("completed_at").last()

        if not last_job:
            return

        if not self.is_complete:
            return

        return last_job.completed_at

    def get_absolute_url(self):
        return reverse("jobrequest-detail", kwargs={"pk": self.pk})

    def get_project_yaml_url(self):
        f = furl(self.workspace.repo)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        f.path.segments += ["blob", self.sha, "project.yaml"]
        return f.url

    def get_repo_url(self):
        f = furl(self.workspace.repo)

        if not self.sha:
            logger.info("No SHA found", job_request_pk=self.pk)
            return f.url

        f.path.segments += ["tree", self.sha]
        return f.url

    @property
    def is_complete(self):
        if not self.jobs.exists():
            return False

        return all(j.is_complete for j in self.jobs.all())

    @property
    def is_failed(self):
        """
        Has a JobRequst failed?

        We don't consider a JobRequest failed until all Jobs are either
        Completed or Failed.
        """
        if not all(j.is_failed or j.is_complete for j in self.jobs.all()):
            return False

        return any(j.is_failed for j in self.jobs.all())

    @property
    def is_in_progress(self):
        return any(j.is_in_progress for j in self.jobs.all())

    @property
    def is_pending(self):
        return all(j.is_pending for j in self.jobs.all())

    @property
    def num_completed(self):
        return len([j for j in self.jobs.all() if j.is_complete])

    @property
    def runtime(self):
        if self.started_at is None:
            return

        end = timezone.now() if self.completed_at is None else self.completed_at
        delta = end - self.started_at

        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds))

    @property
    def started_at(self):
        first_job = self.jobs.exclude(started_at=None).order_by("started_at").first()

        if not first_job:
            return

        return first_job.started_at

    @property
    def status(self):
        if self.is_complete:
            return "Completed"

        if self.is_failed:
            return "Failed"

        if self.is_in_progress:
            return "In Progress"

        if self.is_pending:
            return "Pending"

        return "Pending"


class Stats(models.Model):
    """
    This holds Site wide statistics.

    It acts as a singleton by overriding the save() method to always point to
    PK=1.
    """

    api_last_seen = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.pk = 1

        return super().save(*args, **kwargs)


class User(AbstractUser):
    @property
    def name(self):
        """Unify the available names for a User."""
        return self.get_full_name() or self.username
