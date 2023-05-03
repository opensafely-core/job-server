from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField

from .outputs import ReleaseFilePublishRequest


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
    def is_published(self):
        return (
            hasattr(self, "publish_request")
            and self.publish_request.decision_at
            and self.publish_request.decision == ReportPublishRequest.Decisions.APPROVED
        )


class ReportPublishRequest(models.Model):
    class Decisions(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    release_file_publish_request = models.OneToOneField(
        "ReleaseFilePublishRequest",
        on_delete=models.CASCADE,
        related_name="report_publish_request",
    )
    report = models.OneToOneField(
        "Report",
        on_delete=models.CASCADE,
        related_name="publish_request",
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="report_publish_requests_created",
    )

    decision_at = models.DateTimeField(null=True)
    decision_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="report_publish_requests_decisions",
        null=True,
    )
    decision = models.TextField(choices=Decisions.choices, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="report_publish_requests_updated",
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

    @classmethod
    def create_from_report(cls, *, report, user):
        if report is None:
            return None

        if not hasattr(report, "analysis_request"):
            raise Exception("bad type of report??")

        with transaction.atomic():
            # create a request to publish the released file underpinning the report
            rfile_publish_request = ReleaseFilePublishRequest.objects.create(
                created_by=user, workspace=report.release_file.workspace
            )
            rfile_publish_request.files.add(report.release_file)

            # create a request to publish the report
            return ReportPublishRequest.objects.create(
                report=report,
                release_file_publish_request=rfile_publish_request,
                created_by=user,
                updated_by=user,
            )

    def __str__(self):
        return f"Publish request for report: {self.report.title}"

    @transaction.atomic()
    def approve(self, *, user):
        now = timezone.now()

        self.decision_at = now
        self.decision_by = user
        self.decision = self.Decisions.APPROVED
        self.save(update_fields=["decision_at", "decision_by", "decision"])

        self.release_file_publish_request.approve(user=user, now=now)

    def get_approve_url(self):
        return reverse(
            "staff:report-publish-request-approve",
            kwargs={"pk": self.pk},
        )

    def get_staff_url(self):
        return reverse(
            "staff:report-publish-request-detail",
            kwargs={"pk": self.pk},
        )
