from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from ulid import ULID

from jobserver.authorization import CoreDeveloper, has_role
from jobserver.models.common import new_ulid_str


class AnalysisRequest(models.Model):
    id = models.CharField(  # noqa: A003
        default=new_ulid_str, max_length=26, primary_key=True, editable=False
    )

    job_request = models.OneToOneField(
        "jobserver.JobRequest",
        on_delete=models.PROTECT,
        related_name="analysis_request",
    )
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.PROTECT,
        related_name="analysis_requests",
    )
    report = models.OneToOneField(
        "jobserver.Report",
        on_delete=models.SET_NULL,
        related_name="analysis_request",
        null=True,
    )

    title = models.TextField()
    slug = models.SlugField(max_length=255, unique=True)
    purpose = models.TextField()

    # we capture this in the form before the analysis is run so we know what to
    # set report.title to when automatically generating that. Once the Report
    # object exists, this is no longer used
    report_title = models.TextField()

    # store the analysis-specific templating context here.  The schema of this
    # data could entirely change between version or analysis.
    template_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="analysis_requests",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="analysis_requests_updated",
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
                condition=Q(updated_at__isnull=False, updated_by__isnull=False),
                name="%(app_label)s_%(class)s_both_updated_at_and_updated_by_set",
            ),
        ]

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse(
            "interactive:analysis-detail",
            kwargs={
                "project_slug": self.project.slug,
                "slug": self.slug,
            },
        )

    def get_publish_url(self):
        return reverse(
            "interactive:publish-request-create",
            kwargs={
                "project_slug": self.project.slug,
                "slug": self.slug,
            },
        )

    def get_staff_url(self):
        return reverse("staff:analysis-request-detail", kwargs={"slug": self.slug})

    def get_edit_url(self):
        # TODO: decide if this should be the canonical way to edit reports once reports arrive in this project
        return reverse(
            "interactive:report-edit",
            kwargs={
                "project_slug": self.project.slug,
                "slug": self.slug,
            },
        )

    @property
    def publish_request(self):
        """
        Return the publish request tied to this AnalysisRequest's report

        We don't want to relate an AnalysisRequest to a PublishRequest since
        that will couple it to Interactive, when a PublishRequest is intended
        to be a generic object for reports.  However, an AnalysisRequest has a
        nullable relation to Report so we can use that.
        """
        if not self.report:
            return None

        return self.report.publish_requests.order_by("-created_at").first()

    @property
    def report_content(self):
        if not self.report:
            return ""

        path = self.report.release_file.absolute_path()
        if not path.exists():
            return ""

        return path.read_text()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{self.pk}"

        return super().save(*args, **kwargs)

    @property
    def status(self):
        """
        Expose the status of an Analysis

        This builds on top of JobRequest.status, which is deriving a single
        state from its related Jobs.  However we also need to account for the
        job having finished but the output not having been released.
        """
        jr_status = self.job_request.status
        if jr_status != "succeeded":
            return jr_status

        # when the JobRequest has succeeded we still need to check if there has
        # been a file released by looking for a related Report.
        # TODO: handle manual overrides here too
        if not self.report:
            return "awaiting report"

        return jr_status

    @property
    def ulid(self):
        return ULID.from_str(self.id)

    def visible_to(self, user):
        return self.created_by == user or has_role(user, CoreDeveloper)
