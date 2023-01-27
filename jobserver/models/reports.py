from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField


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

    def __str__(self):
        return f"Publish request for report: {self.report.title}"
