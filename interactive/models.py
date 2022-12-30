from django.db import models
from django.utils import timezone
from furl import furl
from timeflake.extensions.django import TimeflakePrimaryKeyBinary

from jobserver.authorization import CoreDeveloper, has_role


class AnalysisRequest(models.Model):
    id = TimeflakePrimaryKeyBinary(  # noqa: A003
        error_messages={"invalid": "Invalid timeflake id"}
    )

    job_request = models.OneToOneField(
        "jobserver.JobRequest",
        on_delete=models.PROTECT,
        related_name="analysis_request",
    )
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.PROTECT,
        related_name="analysis_requests",
    )

    title = models.TextField()
    codelist_slug = models.TextField()
    codelist_name = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    commit_sha = models.TextField()

    complete_email_sent_at = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="analysis_requests",
    )

    def __str__(self):
        return f"{self.title} ({self.codelist_slug})"

    def get_codelist_url(self):
        oc = furl("https://www.opencodelists.org/codelist/")
        return (oc / self.codelist_slug).url

    def visible_to(self, user):
        return self.created_by == user or has_role(user, CoreDeveloper)
