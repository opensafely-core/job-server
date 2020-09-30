import datetime

import pytz
import requests
from django.db import models
from django.urls import reverse

from .runtime import Runtime


class Workspace(models.Model):
    DB_OPTIONS = (
        ("dummy", "Dummy database"),
        ("slice", "Cut-down (but real) database"),
        ("full", "Full database"),
    )
    name = models.TextField()
    repo = models.TextField(db_index=True)
    branch = models.TextField()
    owner = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    db = models.TextField(choices=DB_OPTIONS)

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
    force_run_dependencies = models.BooleanField(default=False)
    started = models.BooleanField(default=False)
    action_id = models.TextField()
    backend = models.TextField(db_index=True)
    status_code = models.IntegerField(null=True, blank=True)
    status_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    callback_url = models.TextField(null=True, blank=True)
    needed_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
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

    def get_absolute_url(self):
        return reverse("job-detail", kwargs={"pk": self.pk})

    def notify_callback_url(self):
        if not self.callback_url:
            return

        # A new dependency has been added; notify the originating thread
        if self.needed_by and not self.started:
            status = f"Starting dependency {self.action}, job#{self.pk}"
        elif self.started and self.completed_at:
            if self.status_code == 0:
                status = f"{self.action} finished: {self.status_message})"
            else:
                status = f"Error in {self.action} (status {self.status_message})"

        requests.post(self.callback_url, json={"message": status})

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
        if self.status_code is not None:
            if self.status_code == 6:
                return "Pending"

            if self.status_code == 7:
                return "Dependency Failed"

            return "Failed"

        if self.started_at and not self.completed_at:
            return "In Progress"

        if not (self.started_at and self.completed_at):
            return "Pending"

        if self.completed_at:
            return "Completed"

    def save(self, *args, **kwargs):
        if self.started:
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
