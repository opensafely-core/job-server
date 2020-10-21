import datetime

import networkx as nx
import pytz
import requests
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from first import first

from .runtime import Runtime


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

    def __str__(self):
        return f"{self.action_id} ({self.pk})"

    @property
    def edge(self):
        if not self.needed_by_id:
            return

        return (self.pk, self.needed_by_id)

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
    requested_action = models.TextField()
    callback_url = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def completed_at(self):
        if not self.ordered_jobs:
            return

        if not self.is_complete:
            return

        return first(reversed(self.ordered_jobs)).completed_at

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
    def ordered_jobs(self):
        """Order this JobRequest's Jobs based on their dependencies."""
        # cache jobs QuerySet to memory to avoid further queries
        all_jobs = list(self.jobs.all())

        if len(all_jobs) == 1:
            return [first(all_jobs)]

        # create a lookup table of Job ID -> Job so we can convert the graph
        # nodes (Job IDs) back to Job instances
        jobs_by_id = {j.pk: j for j in all_jobs}

        # build up a list of edges using Job's edge property, no edge means
        # it's a root node
        edges = [j.edge for j in all_jobs if j.edge]

        # build a directed graph from the edges so we can get a linear
        # representation of them
        graph = nx.DiGraph(edges)

        # convert graph to a linear iterable.  topological_sort() is a roughly
        # linear representation of the graph.  This will, of course, fall down
        # for graphs with multiple forks but that's a known issue.
        return [jobs_by_id[pk] for pk in nx.topological_sort(graph)]

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
    def started_at(self):
        if not self.ordered_jobs:
            return

        return first(self.ordered_jobs).started_at

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


class User(AbstractUser):
    pass
