from datetime import timedelta

import structlog
from django.db import models
from django.urls import reverse
from django.utils import timezone
from opentelemetry.trace import propagation
from opentelemetry.trace.propagation import tracecontext

from ..runtime import Runtime


logger = structlog.get_logger(__name__)


class JobManager(models.Manager):
    use_in_migrations = True

    def previous(self, job):
        workspace = job.job_request.workspace
        backend = job.job_request.backend
        action = job.action
        return (
            super()
            .filter(
                job_request__workspace=workspace,
                job_request__backend=backend,
                action=action,
                id__lt=job.id,
            )
            .order_by("created_at")
            .last()
        )


class Job(models.Model):
    """
    The execution of an action on a Backend

    We expect this model to only be written to, via the API, by a job-runner.
    """

    objects = JobManager()

    job_request = models.ForeignKey(
        "JobRequest",
        on_delete=models.PROTECT,
        related_name="jobs",
    )

    # The unique identifier created by job-runner to reference this Job.  We
    # trust whatever job-runner sets this to.
    identifier = models.TextField(unique=True)

    action = models.TextField()
    run_command = models.TextField(default="")

    # The current state of the Job, as defined by job-runner.
    status = models.TextField()
    status_code = models.TextField(default="", blank=True)
    status_message = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    # send from job-runner so we can link direct to a trace
    trace_context = models.JSONField(null=True)

    metrics = models.JSONField(null=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.action} ({self.pk})"

    def get_absolute_url(self):
        return reverse(
            "job-detail",
            kwargs={
                "project_slug": self.job_request.workspace.project.slug,
                "workspace_slug": self.job_request.workspace.name,
                "pk": self.job_request.pk,
                "identifier": self.identifier,
            },
        )

    def get_cancel_url(self):
        return reverse(
            "job-cancel",
            kwargs={
                "project_slug": self.job_request.workspace.project.slug,
                "workspace_slug": self.job_request.workspace.name,
                "pk": self.job_request.pk,
                "identifier": self.identifier,
            },
        )

    def get_redirect_url(self):
        return reverse("job-redirect", kwargs={"identifier": self.identifier})

    @property
    def is_completed(self):
        return self.status in ["failed", "succeeded"]

    @property
    def is_missing_updates(self):
        """
        Is this Job missing expected updates from job-runner?

        When a Job has yet to finish but we haven't had an update from
        job-runner in >30 minutes we want to show users a warning.
        """
        if self.is_completed:
            # Job has completed, ignore lack of updates
            return False

        if not self.updated_at:
            # we can't check freshness without updated_at
            return False

        now = timezone.now()
        threshold = timedelta(minutes=30)
        delta = now - self.updated_at

        return delta > threshold

    @property
    def runtime(self):
        if not self.is_completed:
            return Runtime(0, 0, 0)

        if self.started_at is None or self.completed_at is None:
            return Runtime(0, 0, 0)

        delta = self.completed_at - self.started_at
        total_seconds = delta.total_seconds()

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return Runtime(int(hours), int(minutes), int(seconds), int(total_seconds))

    @property
    def trace_id(self):
        if not self.trace_context:
            return None  # pragma: no cover

        # this rediculous dance is just because of OTel spec silliness
        ctx = tracecontext.TraceContextTextMapPropagator().extract(
            carrier=self.trace_context
        )
        span_ctx = propagation.get_current_span(ctx).get_span_context()
        return span_ctx.trace_id
