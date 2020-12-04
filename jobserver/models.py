import base64
import secrets

import requests
import structlog
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_slug
from django.db import models
from django.urls import reverse
from django.utils import timezone
from furl import furl

from .backends import BACKEND_CHOICES
from .runtime import Runtime


logger = structlog.get_logger(__name__)


def new_id():
    """
    Return a random 16 character lowercase alphanumeric string
    We used to use UUID4's but they are unnecessarily long for our purposes
    (particularly the hex representation) and shorter IDs make debugging
    and inspecting the job-runner a bit more ergonomic.
    """
    return base64.b32encode(secrets.token_bytes(10)).decode("ascii").lower()


class Job(models.Model):
    # TODO: remove nullability after move to v2
    job_request = models.ForeignKey(
        "JobRequest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="jobs",
    )

    # The unique identifier created by job-runner to reference this Job.  We
    # trust whatever job-runner sets this to.
    identifier = models.TextField(unique=True)

    action = models.TextField()

    # The current state of the Job, as defined by job-runner.
    status = models.TextField()
    status_message = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Remove after the move to v2
    started = models.BooleanField(default=False)
    status_code = models.IntegerField(null=True, blank=True)
    needed_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.action} ({self.pk})"

    def get_absolute_url(self):
        return reverse("job-detail", kwargs={"identifier": self.identifier})

    def get_zombify_url(self):
        return reverse("job-zombify", kwargs={"identifier": self.identifier})

    def notify_callback_url(self):
        if not self.job_request.callback_url:
            return

        # A new dependency has been added; notify the originating thread
        if self.needed_by and not self.started:
            status = f"Starting dependency {self.action}, job#{self.pk}"
        elif self.started and self.completed_at:
            if self.status_code == 0:
                status = f"{self.action} finished: {self.status_message}"
            else:
                status = f"Error in {self.action} (status {self.status_message})"
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.notify_callback_url()


class JobRequest(models.Model):
    """
    A request to run a Job

    This represents the request, from a Human, to run a given Job in a
    Workspace.  The job-runner will create any required Jobs for the requested
    one to run.  All Jobs, either added by Human or Computer, are then grouped
    by this object.
    """

    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="job_requests",
    )
    workspace = models.ForeignKey(
        "Workspace", on_delete=models.CASCADE, related_name="job_requests"
    )

    backend = models.TextField(choices=BACKEND_CHOICES, db_index=True)
    force_run_dependencies = models.BooleanField(default=False)
    requested_actions = models.JSONField()
    callback_url = models.TextField(default="", blank=True)
    sha = models.TextField()
    identifier = models.TextField(default=new_id, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("job-request-detail", kwargs={"pk": self.pk})

    @property
    def completed_at(self):
        last_job = self.jobs.order_by("completed_at").last()

        if not last_job:
            return

        if not self.status == "succeeded":
            return

        return last_job.completed_at

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
    def num_completed(self):
        return len([j for j in self.jobs.all() if j.status == "succeeded"])

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
        statuses = self.jobs.values_list("status", flat=True)

        # when they're all the same, just use that
        if len(set(statuses)) == 1:
            return statuses[0]

        # if any status is running then the JobRequest is running
        if "running" in statuses:
            return "running"

        # if we have a mix of failed and succeeded then we've failed
        if {"failed", "succeeded"} == set(statuses):
            return "failed"

        # if we have a mix of pending, failed, and succeeded BUT no running
        # then we're still running.
        some_failed = "failed" in statuses
        some_succeeded = "succeeded" in statuses
        some_completed = some_failed or some_succeeded
        if "pending" in statuses and some_completed:
            return "running"

        return "unknown"


class Stats(models.Model):
    """
    This holds Site wide statistics.

    It acts as a singleton by overriding the save() method to always point to
    PK=1.
    """

    api_last_seen = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1

        return super().save(*args, **kwargs)


class User(AbstractUser):
    @property
    def name(self):
        """Unify the available names for a User."""
        return self.get_full_name() or self.username


class Workspace(models.Model):
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workspaces",
    )

    name = models.TextField(unique=True, validators=[validate_slug])
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
        return reverse("workspace-detail", kwargs={"name": self.name})

    def get_latest_status_for_action(self, action):
        """
        Get the latest status for an action in this Workspace
        """

        try:
            job = Job.objects.filter(action=action, job_request__workspace=self).latest(
                "created_at"
            )
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
