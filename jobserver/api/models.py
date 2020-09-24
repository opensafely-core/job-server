import datetime

import pytz
import requests
from django.db import models
from django.db.models.signals import post_save


class Workspace(models.Model):
    DB_OPTIONS = (
        ("dummy", "Dummy database"),
        ("slice", "Cut-down (but real) database"),
        ("full", "Full database"),
    )
    name = models.CharField(max_length=100)
    repo = models.CharField(db_index=True, max_length=300)
    branch = models.CharField(max_length=200)
    owner = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    db = models.CharField(max_length=20, choices=DB_OPTIONS)

    def __str__(self):
        return f"{self.name} ({self.repo})"


class Job(models.Model):
    force_run = models.BooleanField(default=False)
    force_run_dependencies = models.BooleanField(default=False)
    started = models.BooleanField(default=False)
    action_id = models.CharField(max_length=200)
    backend = models.CharField(max_length=20, db_index=True)
    status_code = models.IntegerField(null=True, blank=True)
    status_message = models.CharField(null=True, blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    callback_url = models.CharField(max_length=200, null=True, blank=True)
    needed_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    workspace = models.ForeignKey(
        Workspace,
        related_name="workspaces",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.action_id} ({self.pk})"

    @property
    def status(self):
        if not (self.started_at and self.completed_at):
            return "Pending"

        if self.started_at and not self.completed_at:
            return "In Progress"

        if self.completed_at:
            return "Completed"

    def save(self, *args, **kwargs):
        if self.started and not self.started_at:
            self.started_at = datetime.datetime.now(tz=pytz.UTC)
        if self.status_code is not None and not self.completed_at:
            if self.started:
                self.completed_at = datetime.datetime.now(tz=pytz.UTC)
        super().save(*args, **kwargs)


class JobOutput(models.Model):
    location = models.CharField(max_length=300)
    job = models.ForeignKey(
        Job, null=True, blank=True, related_name="outputs", on_delete=models.SET_NULL
    )


def notify_callback_url(sender, instance, created, raw, using, update_fields, **kwargs):
    """Send a message to slack about the job"""
    if sender == Job and instance.callback_url:
        if sender == Job:
            if instance.needed_by and not instance.started:
                # A new dependency has been added; notify the originating thread
                requests.post(
                    instance.callback_url,
                    json={
                        "message": f"Starting dependency {instance.action}, job#{instance.pk}"
                    },
                )
            elif instance.started and instance.completed_at:
                if instance.status_code == 0:
                    status = f"{instance.action} finished: {instance.status_message})"
                else:
                    status = (
                        f"Error in {instance.action} (status {instance.status_message})"
                    )
                requests.post(instance.callback_url, json={"message": status})


post_save.connect(notify_callback_url)
