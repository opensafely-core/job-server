from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField

from .outputs import ReleaseFilePublishRequest


class Report(models.Model):
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

    published_at = models.DateTimeField(null=True)
    published_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_published",
        null=True,
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
                        published_at__isnull=True,
                        published_by__isnull=True,
                    )
                    | (
                        Q(
                            published_at__isnull=False,
                            published_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_published_at_and_published_by_set",
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

    def get_staff_url(self):
        return reverse("staff:report-detail", kwargs={"pk": self.pk})


class ReportPublishRequest(models.Model):
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

    approved_at = models.DateTimeField(null=True)
    approved_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="report_publish_requests_approved",
        null=True,
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="report_publish_requests_created",
    )

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
                        approved_at__isnull=True,
                        approved_by__isnull=True,
                    )
                    | (
                        Q(
                            approved_at__isnull=False,
                            approved_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_approved_at_and_approved_by_set",
            ),
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

        self.approved_at = now
        self.approved_by = user
        self.save(update_fields=["approved_at", "approved_by"])

        self.report.published_at = now
        self.report.published_by = user
        self.report.save(update_fields=["published_at", "published_by"])

        self.release_file_publish_request.approve(user=user, now=now)

    def get_absolute_url(self):
        return reverse(
            "interactive:report-publish-request-update",
            kwargs={
                "org_slug": self.report.analysis_request.project.org.slug,
                "project_slug": self.report.analysis_request.project.slug,
                "slug": self.report.analysis_request.slug,
                "pk": self.pk,
            },
        )
