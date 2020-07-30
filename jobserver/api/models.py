import datetime
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

    def save(self, *args, **kwargs):
        if self.completed_at:
            raise ValidationError("Job has already been completed")
        if self.started and not self.started_at:
            self.started_at = datetime.datetime.now()
        if self.status_code is not None and not self.completed_at:
            if not self.started:
                raise ValidationError("Cannot complete a job that has not started ")
            self.completed_at = datetime.datetime.now()
        super().save(*args, **kwargs)


def notify_callback_url(sender, instance, created, raw, using, update_fields, **kwargs):
    """Send a message to slack about the job
    """
    if sender == Job and instance.callback_url and instance.completed_at:
        if instance.status_code == 0:
            status = f"Finished. See {instance.output_url}"
        else:
            status = f"Error (status {instance.status_message})"
        requests.post(instance.callback_url, json={"message": status})


post_save.connect(notify_callback_url)
