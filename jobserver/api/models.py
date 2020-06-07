import datetime
from django.db import models
from django.core.exceptions import ValidationError


class Job(models.Model):
    repo = models.CharField(db_index=True, max_length=300)
    tag = models.CharField(max_length=200)
    started = models.BooleanField(default=False)
    operation = models.CharField(max_length=20)
    status_code = models.IntegerField(null=True, blank=True)
    output_url = models.CharField(null=True, blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.completed_at:
            raise ValidationError("Job has already been completed")
        if self.started and not self.started_at:
            self.started_at = datetime.datetime.now()
        if self.status_code and not self.completed_at:
            if not self.started:
                raise ValidationError("Cannot complete a job that has not started ")
            self.completed_at = datetime.datetime.now()
        super().save(*args, **kwargs)
