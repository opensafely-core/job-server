import structlog
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from furl import furl


logger = structlog.get_logger(__name__)


class Project(models.Model):
    """
    A public-facing grouping of work on a topic.

    This includes the Workspaces where work is done, the Repos for the code
    driving that work, the IG approvals allowing the work to happen, and any
    Papers which are produced as a result of the work.
    """

    class Statuses(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        POSTPONED = "postponed", "Postponed"
        RETIRED = "retired", "Retired"

        # we expect these to go away and be replaced with first class support
        # for linking out to papers and reports but for now we need to track
        # them so they're statuses.
        ONGOING_LINKED = "ongoing-and-linked", "Ongoing - paper/report linked"
        COMPLETED_LINKED = "completed-and-linked", "Completed - paper/report linked"
        COMPLETED_AWAITING = (
            "completed-and-awaiting",
            "Completed - awaiting paper/report",
        )

    copilot = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="copiloted_projects",
    )

    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    number = models.IntegerField(null=True)

    copilot_support_ends_at = models.DateTimeField(null=True)

    status = models.TextField(choices=Statuses.choices, default=Statuses.ONGOING)
    status_description = models.TextField(default="", blank=True)

    copilot_notes = models.TextField(default="", blank=True)

    # OSI applications will be done externally.
    # Unfortunately we can't validate this in the db with a CheckConstraint
    # because we can't reference the FK's related_name there.
    application_url = models.TextField(default="")

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_projects",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="projects_updated",
        null=True,
    )

    class Meta:
        constraints = [
            # only consider uniqueness of number when it's not null
            models.UniqueConstraint(
                fields=["number"],
                name="unique_number_ignore_null",
                condition=Q(number__isnull=False),
            ),
            models.CheckConstraint(
                check=~Q(slug=""),
                name="slug_is_not_empty",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "project-detail",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_approved_url(self):
        f = furl("https://www.opensafely.org/approved-projects")

        if self.number:
            f.fragment = f"project-{self.number}"

        return f.url

    def get_edit_url(self):
        return reverse(
            "project-edit",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_interactive_url(self):
        return reverse(
            "interactive:analysis-create",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_logs_url(self):
        return reverse(
            "project-event-log",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_releases_url(self):
        return reverse(
            "project-release-list",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_reports_url(self):
        return reverse(
            "project-report-list",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_staff_url(self):
        return reverse("staff:project-detail", kwargs={"slug": self.slug})

    def get_staff_edit_url(self):
        return reverse("staff:project-edit", kwargs={"slug": self.slug})

    @property
    def interactive_slug(self):
        return f"{self.slug}-interactive"

    @property
    def interactive_workspace(self):
        return self.workspaces.get(name=self.interactive_slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    @property
    def title(self):
        if self.number is None:
            return self.name

        return f"{self.number} - {self.name}"
