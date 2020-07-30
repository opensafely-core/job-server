import datetime
import pytz
import requests

from django.db import models
from django.db.models.signals import post_save


class Job(models.Model):
    repo = models.CharField(db_index=True, max_length=300)
    tag = models.CharField(max_length=200)
    started = models.BooleanField(default=False)
    operation = models.CharField(max_length=20)
    backend = models.CharField(max_length=20, db_index=True)
    db = models.CharField(max_length=20)
    status_code = models.IntegerField(null=True, blank=True)
    status_message = models.CharField(null=True, blank=True, max_length=200)
    output_url = models.CharField(null=True, blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    callback_url = models.CharField(max_length=200, null=True, blank=True)
    needed_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )

    def save(self, *args, **kwargs):
        if self.started and not self.started_at:
            self.started_at = datetime.datetime.now(tz=pytz.UTC)
        if self.status_code is not None and not self.completed_at:
            if self.started:
                self.completed_at = datetime.datetime.now(tz=pytz.UTC)
        super().save(*args, **kwargs)


def notify_callback_url(sender, instance, created, raw, using, update_fields, **kwargs):
    """Send a message to slack about the job
    """
    if sender == Job and instance.callback_url:
        if sender == Job:
            if instance.needed_by and not instance.started:
                # A new dependency has been added; notify the originating thread
                requests.post(
                    instance.callback_url,
                    json={
                        "message": f"Starting dependency {instance.operation}, job#{instance.pk}"
                    },
                )
            elif instance.started and instance.completed_at:
                if instance.status_code == 0:
                    status = f"{instance.operation} finished. See {instance.output_url}"
                else:
                    status = f"Error in {instance.operation} (status {instance.status_message})"
            requests.post(instance.callback_url, json={"message": status})


post_save.connect(notify_callback_url)
