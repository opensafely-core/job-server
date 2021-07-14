from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from ulid import ULID

from jobserver.models.common import new_ulid_str


def absolute_file_path(path):
    abs_path = settings.RELEASE_STORAGE / path
    return abs_path


class PublicRelease(models.Model):
    """
    A Release for a Workspace which has been, or will be made publicly available
    """

    class Statuses(models.TextChoices):
        DRAFT = "draft", "Draft"
        LIVE = "live", "Live"

    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="public_releases",
    )
    files = models.ManyToManyField(
        "ReleaseFile",
        related_name="public_releases",
    )
    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="public_releases",
    )

    status = models.TextField(choices=Statuses.choices, default=Statuses.DRAFT)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.status} Public Release made by {self.created_by.username}"


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
    created_at = models.DateTimeField(default=timezone.now)
    # the user who requested the release
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="releases",
    )
    status = models.TextField(choices=Statuses.choices, default=Statuses.REQUESTED)

    # list of files requested for release
    requested_files = models.JSONField()

    def get_absolute_url(self):
        return reverse(
            "release-detail",
            kwargs={
                "org_slug": self.workspace.project.org.slug,
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.id,
            },
        )

    def get_api_url(self):
        return reverse("api:release", kwargs={"release_id": self.id})


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
    created_at = models.DateTimeField(default=timezone.now)
    # the user who approved the release
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="released_files",
    )
    # name is path from the POV of the researcher, e.g "outputs/file1.txt"
    name = models.TextField()
    # path is from the POV of the system e.g. "workspace/releases/RELEASE_ID/file1.txt"
    path = models.TextField()
    # the sha256 hash of the file
    filehash = models.TextField()

    def absolute_path(self):
        return absolute_file_path(self.path)

    def get_absolute_url(self):
        return reverse(
            "release-detail",
            kwargs={
                "org_slug": self.release.workspace.project.org.slug,
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "pk": self.release.id,
                "path": self.name,
            },
        )

    def get_api_url(self):
        """The API url that will serve up this file."""
        return reverse(
            "api:release-file",
            kwargs={
                "release_id": self.release.id,
                "filename": self.name,
            },
        )
