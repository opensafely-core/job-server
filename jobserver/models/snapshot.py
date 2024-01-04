import structlog
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .publish_request import PublishRequest


logger = structlog.get_logger(__name__)


class Snapshot(models.Model):
    """A "frozen" copy of the ReleaseFiles for a Workspace."""

    class Statuses(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    files = models.ManyToManyField(
        "ReleaseFile",
        related_name="snapshots",
    )
    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="snapshots",
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="snapshots",
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
        ]

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"{status} Snapshot made by {self.created_by.username}"

    def get_absolute_url(self):
        return reverse(
            "workspace-snapshot-detail",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.pk,
            },
        )

    def get_api_url(self):
        return reverse(
            "api:snapshot",
            kwargs={
                "workspace_id": self.workspace.name,
                "snapshot_id": self.pk,
            },
        )

    def get_download_url(self):
        return reverse(
            "workspace-snapshot-download",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.pk,
            },
        )

    def get_publish_api_url(self):
        return reverse(
            "api:snapshot-publish",
            kwargs={
                "workspace_id": self.workspace.name,
                "snapshot_id": self.pk,
            },
        )

    @property
    def is_draft(self):
        return not self.is_published

    @property
    def is_published(self):
        # We support multiple publish requests over time but we only look at
        # the latest one to get published/draft status.
        latest = self.publish_requests.order_by("-created_at").first()

        if not latest:
            return False

        return latest.decision == PublishRequest.Decisions.APPROVED
