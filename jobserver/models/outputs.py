import json
import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def absolute_file_path(path):
    abs_path = settings.RELEASE_STORAGE / path
    return abs_path


class Release(models.Model):
    """A set of reviewed and redacted outputs from a Workspace"""

    # No value in the default Autoid as we are using a content-addressable hash
    # as it. Additionaly it avoids enumeration attacks.
    id = models.TextField(primary_key=True)

    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="releases",
    )
    backend = models.ForeignKey(
        "Backend",
        on_delete=models.PROTECT,
        related_name="+",
    )
    created_at = models.DateTimeField(default=timezone.now)
    # TODO: once we have new review flow, this can be made null=False, as we'll
    # have the correct user.
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    upload_dir = models.TextField()
    # store local TPP/EMIS username for audit
    backend_user = models.TextField()

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

    def get_api_index_url(self):
        return reverse("release-index", kwargs={"release_hash": self.id})

    @property
    def manifest(self):
        path = os.path.join(self.upload_dir, "metadata/manifest.json")
        return json.loads(absolute_file_path(path).read_text())


class ReleaseFile(models.Model):
    """Individual files in a Release.

    We store these in the file system to avoid db bloat and so that we can
    serve them via nginx.
    """

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
    # name is path from the POV of the researcher, e.g "outputs/file1.txt"
    name = models.TextField()
    # path is from the POV of the system e.g. "workspace/release/outputs/file1.txt"
    path = models.TextField()

    def absolute_path(self):
        return absolute_file_path(self.path)

    def get_absolute_url(self):
        return reverse(
            "release-detail-with-path",
            kwargs={
                "org_slug": self.release.workspace.project.org.slug,
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "pk": self.release.id,
                "path": self.path,
            },
        )

    def get_api_url(self):
        """The API url that will serve up this file."""
        return reverse(
            "release-file",
            kwargs={
                "release_hash": self.release.id,
                "filename": self.name,
            },
        )
