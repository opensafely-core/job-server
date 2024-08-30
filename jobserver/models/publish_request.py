import structlog
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from jobserver.utils import set_from_qs


logger = structlog.get_logger(__name__)


class PublishRequest(models.Model):
    class Decisions(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    # a convenience link to a report if one exists
    report = models.ForeignKey(
        "Report",
        on_delete=models.PROTECT,
        related_name="publish_requests",
        null=True,
    )
    snapshot = models.ForeignKey(
        "Snapshot",
        on_delete=models.CASCADE,
        related_name="publish_requests",
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
        related_name="publish_requests",
    )

    decision_at = models.DateTimeField(null=True)
    decision_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="publish_requests_decisions",
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
                condition=(
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

    class IncorrectReportError(Exception):
        pass

    class MultipleWorkspacesFound(Exception):
        pass

    def __str__(self):
        return f"Publish request for Snapshot={self.snapshot.pk}"

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
    def create_from_files(cls, *, files, report=None, user):
        """
        Create a PublishRequest from the given files.

        This will create a new snapshot if one doesn't already exist for the
        given files and workspace.

        If either the snapshot or a pending publish request already exist those
        objects will be returned instead of raising an error.
        """
        # avoid circular imports
        from .snapshot import Snapshot
        from .workspace import Workspace

        # only look at files which haven't been deleted (redacted)
        files = [f for f in files if not f.is_deleted]

        try:
            workspace = Workspace.objects.get(pk__in={f.workspace_id for f in files})
        except Workspace.MultipleObjectsReturned:
            raise cls.MultipleWorkspacesFound

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
            updated_by=user,
            report=report,
            snapshot=snapshot,
            workspace=workspace,
        )

    @classmethod
    def create_from_report(self, *, report, user):
        """Convenience wrapper for reports"""
        return PublishRequest.create_from_files(
            files=[report.release_file],
            report=report,
            user=user,
        )

    def get_approve_url(self):
        return reverse(
            "staff:publish-request-approve",
            kwargs={
                "pk": self.report.pk,
                "publish_request_pk": self.pk,
            },
        )

    def get_reject_url(self):
        return reverse(
            "staff:publish-request-reject",
            kwargs={
                "pk": self.report.pk,
                "publish_request_pk": self.pk,
            },
        )

    @property
    def is_approved(self):
        return self.decision == self.Decisions.APPROVED

    @property
    def is_pending(self):
        return self.decision is None

    @property
    def is_rejected(self):
        return self.decision == self.Decisions.REJECTED

    def reject(self, *, user):
        self.decision_at = timezone.now()
        self.decision_by = user
        self.decision = self.Decisions.REJECTED
        self.save(update_fields=["decision_at", "decision_by", "decision"])

    def save(self, *args, **kwargs):
        # check our convenience FK points at the right report for this publish
        # request by checking the reports release file is in our target
        # snapshot
        if self.report and self.report.release_file not in self.snapshot.files.all():
            raise self.IncorrectReportError()

        return super().save(*args, **kwargs)
