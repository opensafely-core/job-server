import structlog
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField

from .publish_request import PublishRequest


logger = structlog.get_logger(__name__)


class Report(models.Model):
    project = models.ForeignKey(
        "Project",
        on_delete=models.PROTECT,
        related_name="reports",
    )
    release_file = models.ForeignKey(
        "ReleaseFile",
        on_delete=models.PROTECT,
        related_name="reports",
    )

    title = models.TextField()
    slug = AutoSlugField(max_length=100, populate_from=["title"], unique=True)
    description = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_created",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        created_at__isnull=True,
                        created_by__isnull=True,
                    )
                    | (
                        Q(
                            created_at__isnull=False,
                            created_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_created_at_and_created_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        updated_at__isnull=True,
                        updated_by__isnull=True,
                    )
                    | (
                        Q(
                            updated_at__isnull=False,
                            updated_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_updated_at_and_updated_by_set",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if hasattr(self, "analysis_request"):
            return self.analysis_request.get_absolute_url()
        else:
            # we only have reports tied to analyses currently but we expect
            # that to change in the future so rather than error out send the
            # user _somewhere_.
            return "/"

    def get_staff_url(self):
        return reverse("staff:report-detail", kwargs={"pk": self.pk})

    @property
    def is_draft(self):
        return not self.is_published

    @property
    def is_locked(self):
        latest = self.publish_requests.order_by("-created_at").first()

        if not latest:
            return False

        if latest.decision == PublishRequest.Decisions.REJECTED:
            return False

        return True

    @property
    def is_published(self):
        # We support multiple publish requests over time but we only look at
        # the latest one to get published/draft status.
        latest = self.publish_requests.order_by("-created_at").first()

        if not latest:
            return False

        return latest.decision == PublishRequest.Decisions.APPROVED

    @property
    def published_at(self):
        # We support multiple publish requests over time but we only look at
        # the latest one to get published date.
        latest = self.publish_requests.order_by("-created_at").first()

        if not latest:
            return False

        if latest.decision != PublishRequest.Decisions.APPROVED:
            return False

        return latest.created_at
