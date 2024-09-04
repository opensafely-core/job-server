import structlog
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from ulid import ULID

from jobserver.models.common import new_ulid_str


logger = structlog.get_logger(__name__)


def absolute_file_path(path):
    abs_path = settings.RELEASE_STORAGE / path
    return abs_path


class ReleaseFile(models.Model):
    """Individual files in a Release.

    We store these in the file system to avoid db bloat and so that we can
    serve them via nginx.
    """

    id = models.CharField(  # noqa: A003
        default=new_ulid_str, max_length=26, primary_key=True, editable=False
    )

    @property
    def ulid(self):
        return ULID.from_str(self.id)

    release = models.ForeignKey(
        "Release",
        on_delete=models.PROTECT,
        related_name="files",
    )
    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="files",
    )
    # the user who approved the release

    # name is path from the POV of the researcher, e.g "outputs/file1.txt"
    name = models.TextField()
    # path is from the POV of the system e.g. "workspace/releases/RELEASE_ID/file1.txt"
    path = models.TextField()
    # the sha256 hash of the file
    filehash = models.TextField()
    size = models.IntegerField()  # bytes
    mtime = models.DateTimeField()

    metadata = models.JSONField(null=True)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="released_files",
    )

    deleted_at = models.DateTimeField(null=True)
    deleted_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="deleted_files",
    )

    uploaded_at = models.DateTimeField(null=True)

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
            models.CheckConstraint(
                condition=(
                    Q(
                        deleted_at__isnull=True,
                        deleted_by__isnull=True,
                    )
                    | Q(
                        deleted_at__isnull=False,
                        deleted_by__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_both_deleted_at_and_deleted_by_set",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __format__(self, format_spec):
        match format_spec:
            case "b":
                return f"{self.size:,}b"
            case "Kb":
                value = round(self.size / 1024, 2)
                return f"{value:,}Kb"
            case "Mb":
                value = round(self.size / (1024 * 1024), 2)
                return f"{value:,}Mb"
            case _:
                return super().__format__(format_spec)

    def absolute_path(self):
        return absolute_file_path(self.path)

    def get_absolute_url(self):
        return reverse(
            "release-detail",
            kwargs={
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "pk": self.release.id,
                "path": self.name,
            },
        )

    def get_api_url(self):
        """The API url that will serve up this file."""
        if getattr(self, "is_published", False):
            # This is a hack so the view for viewing a published ReleaseFile
            # can pass down the knowledge that a ReleaseFile has been
            # published, avoid O(N) queries on views which aren't expecting to
            # have to add `.select_related("snapshot")` to a QuerySet.
            return reverse(
                "published-file",
                kwargs={
                    "project_slug": self.workspace.project.slug,
                    "workspace_slug": self.workspace.name,
                    "file_id": self.id,
                },
            )

        return reverse("api:release-file", kwargs={"file_id": self.id})

    def get_delete_url(self):
        return reverse(
            "release-file-delete",
            kwargs={
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "pk": self.release.id,
                "release_file_id": self.id,
            },
        )

    def get_latest_url(self):
        return reverse(
            "workspace-latest-outputs-detail",
            kwargs={
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "path": f"{self.release.backend.slug}/{self.name}",
            },
        )

    @property
    def is_deleted(self):
        """Has the file on disk been deleted?"""
        return self.deleted_at is not None
