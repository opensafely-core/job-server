from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from ulid import ULID

from jobserver.models.common import new_ulid_str
from jobserver.utils import set_from_qs


def absolute_file_path(path):
    abs_path = settings.RELEASE_STORAGE / path
    return abs_path


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

    def get_download_url(self):
        return reverse(
            "release-download",
            kwargs={
                "org_slug": self.workspace.project.org.slug,
                "project_slug": self.workspace.project.slug,
                "workspace_slug": self.workspace.name,
                "pk": self.id,
            },
        )


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
                "org_slug": self.release.workspace.project.org.slug,
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
                    "org_slug": self.workspace.project.org.slug,
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
                "org_slug": self.release.workspace.project.org.slug,
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
                "org_slug": self.release.workspace.project.org.slug,
                "project_slug": self.release.workspace.project.slug,
                "workspace_slug": self.release.workspace.name,
                "path": f"{self.release.backend.slug}/{self.name}",
            },
        )

    @property
    def is_deleted(self):
        """Has the file on disk been deleted?"""
        return self.deleted_at is not None


class ReleaseFileReview(models.Model):
    class Statuses(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    release_file = models.ForeignKey(
        "ReleaseFile",
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    status = models.TextField(choices=Statuses.choices)
    comments = models.JSONField()

    # no default here because this needs to match for all reviews created at
    # the same time.
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="release_file_reviews",
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
                "org_slug": self.workspace.project.org.slug,
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
                "org_slug": self.workspace.project.org.slug,
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

        return latest.decision == SnapshotPublishRequest.Decisions.APPROVED


class SnapshotPublishRequest(models.Model):
    class Decisions(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    snapshot = models.ForeignKey(
        "Snapshot",
        on_delete=models.SET_NULL,
        related_name="publish_requests",
        null=True,
    )
    workspace = models.ForeignKey(
        "Workspace",
        on_delete=models.PROTECT,
        related_name="publish_requests",
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="snapshot_publish_requests",
    )

    decision_at = models.DateTimeField(null=True)
    decision_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="snapshot_publish_requests_decisions",
        null=True,
    )
    decision = models.TextField(choices=Decisions.choices, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="snapshot_requests_updated",
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
                        decision_at__isnull=True,
                        decision_by__isnull=True,
                        decision__isnull=True,
                    )
                    | (
                        Q(
                            decision_at__isnull=False,
                            decision_by__isnull=False,
                            decision__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_decision_at_decision_by_and_decision_set",
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

    @transaction.atomic()
    def approve(self, *, user, now=None):
        if now is None:
            now = timezone.now()

        self.decision_at = now
        self.decision_by = user
        self.decision = self.Decisions.APPROVED
        self.save(update_fields=["decision_at", "decision_by", "decision"])

    @classmethod
    @transaction.atomic()
    def create_from_files(cls, *, files, workspace, user):
        """
        Create a SnapshotPublishRequest from the given files.

        This will create a new snapshot if one doesn't already exist for the
        given files and workspace.

        If either the snapshot or a pending publish request already exist those
        objects will be returned instead of raising an error.
        """
        # only look at files which haven't been deleted (redacted)
        files = [f for f in files if not f.is_deleted]

        # look for an existing snapshots with the same files and workspace.  We
        # can't do an exact filter match across an M2M so first we filter in
        # the DB for any snapshots which match the workspace and any of the
        # files we have.  Then compare the PKs of the given files with those in
        # each snapshot.
        snapshots = Snapshot.objects.filter(
            workspace=workspace, files__in=files
        ).distinct()
        exact_matches = [
            s for s in snapshots if set_from_qs(s.files.all()) == {f.pk for f in files}
        ]

        if len(exact_matches) > 1:
            # this shouldn't happen but we're catching it so we can rely on a
            # snapshot's files being unique inside its workspace
            matches = len(exact_matches)
            raise Snapshot.MultipleObjectsReturned(
                f"Found {matches} snapshots when one was expected"
            )

        if exact_matches:
            snapshot = exact_matches[0]
        else:
            # no existing snapshot in this workspace with these exact files so
            # create one and carry one
            snapshot = Snapshot.objects.create(workspace=workspace, created_by=user)
            snapshot.files.add(*files)

        # There should only ever be one pending publish request for a Snapshot,
        # enforce that here.
        latest_publish_request = snapshot.publish_requests.order_by(
            "-created_at"
        ).first()
        if latest_publish_request and latest_publish_request.decision is None:
            return latest_publish_request

        return cls.objects.create(
            created_by=user,
            snapshot=snapshot,
            workspace=workspace,
        )
