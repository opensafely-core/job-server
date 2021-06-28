import json

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Release(models.Model):
    """Reviewed and redacted outputs from a Workspace"""

    # No value in the default Autoid as we are using a content-addressable hash
    # as it. Additionaly it avoids enumeration attacks.
    id = models.TextField(primary_key=True)
    # TODO: link this formally via backend_username once we have a mapping
    # between User and their backend username
    publishing_user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
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
    published_at = models.DateTimeField(default=timezone.now)
    upload_dir = models.TextField()
    # list of files in the release upload
    files = models.JSONField()
    # store local TPP/EMIS username for audit
    backend_user = models.TextField()

    def get_absolute_url(self):
        return reverse(
            "workspace-release",
            kwargs={
                "org_slug": self.workspace.project.org.slug,
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "release": self.id,
            },
        )

    def file_path(self, filename):
        return settings.RELEASE_STORAGE / self.upload_dir / filename

    @property
    def manifest(self):
        return json.loads(self.file_path("metadata/manifest.json").read_text())
