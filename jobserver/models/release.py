import structlog
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from ulid import ULID

from jobserver.models.common import new_ulid_str


logger = structlog.get_logger(__name__)


class Release(models.Model):
    """A set of reviewed and redacted outputs from a Workspace"""

    class Statuses(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.CharField(  # noqa: A003
        default=new_ulid_str, max_length=26, primary_key=True, editable=False
    )

    @property
    def ulid(self):
        return ULID.from_str(self.id)

    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="releases",
    )
    backend = models.ForeignKey(
        "Backend",
        on_delete=models.PROTECT,
        related_name="releases",
    )
    status = models.TextField(choices=Statuses.choices, default=Statuses.REQUESTED)

    # list of files requested for release
    requested_files = models.JSONField(encoder=DjangoJSONEncoder)

    metadata = models.JSONField(null=True)
    review = models.JSONField(null=True)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="releases",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
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

    def get_absolute_url(self):
        return reverse(
            "release-detail",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.id,
            },
        )

    def get_api_url(self):
        return reverse("api:release", kwargs={"release_id": self.id})

    def get_download_url(self):
        return reverse(
            "release-download",
            kwargs={
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.id,
            },
        )
