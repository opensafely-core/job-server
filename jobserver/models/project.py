import structlog
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import functional, timezone
from django.utils.text import slugify
from furl import furl

from jobserver.project_validators import validate_project_identifier


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

    orgs = models.ManyToManyField(
        "Org",
        related_name="projects",
        through="ProjectCollaboration",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    number = models.IntegerField(
        null=True,
        validators=[validate_project_identifier],
    )

    copilot_support_ends_at = models.DateTimeField(null=True)

    status = models.TextField(choices=Statuses.choices, default=Statuses.ONGOING)
    status_description = models.TextField(default="", blank=True)

    copilot_notes = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="projects_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        created_at__isnull=False,
                        created_by__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_both_created_at_and_created_by_set",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        updated_at__isnull=False,
                        updated_by__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_both_updated_at_and_updated_by_set",
            ),
            # only consider uniqueness of number when it's not null
            models.UniqueConstraint(
                fields=["number"],
                name="unique_number_ignore_null",
                condition=Q(number__isnull=False),
            ),
            models.CheckConstraint(
                condition=~Q(slug=""),
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

        if self.identifier:
            f.fragment = f"project-{self.identifier}"

        return f.url

    def get_edit_url(self):
        return reverse(
            "project-edit",
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

    def get_staff_url(self):
        return reverse("staff:project-detail", kwargs={"slug": self.slug})

    def get_staff_audit_url(self):
        return reverse("staff:project-audit-log", kwargs={"slug": self.slug})

    def get_staff_edit_url(self):
        return reverse("staff:project-edit", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    @property
    def title(self):
        if not self.identifier:
            return self.name

        return f"{self.identifier} - {self.name}"

    @functional.cached_property
    def org(self):
        return self.orgs.filter(collaborations__is_lead=True).first()

    @property
    def identifier(self):
        if self.number in (None, ""):
            return None

        return str(self.number).strip()

    def has_identifier(self):
        return bool(self.identifier)

    def display_identifier(self):
        return self.identifier or ""

    @staticmethod
    def _coerce_numeric_identifiers(values):
        """
        Convert an iterable of raw identifier values into a list of integers.

        Accepts ints (used as-is) and digit-only strings (trimmed and cast to int).
        Any other values—POS-style identifiers, blank strings, None—are ignored.
        """
        numeric_values = []
        for value in values:
            if isinstance(value, int):
                numeric_values.append(value)
                continue

            value_str = str(value).strip()
            if value_str.isdigit():
                numeric_values.append(int(value_str))

        return numeric_values

    @classmethod
    def next_numeric_identifier(cls):
        """
        Return the next sequential project number.

        Fetches all non-null identifiers from the database, coerces the numeric ones,
        and returns max(value) + 1. Returns None if no numeric identifiers exist.
        """
        values = (
            cls.objects.exclude(number__isnull=True)
            .values_list("number", flat=True)
            .iterator()
        )

        numeric_values = cls._coerce_numeric_identifiers(values)
        if not numeric_values:
            return None

        return max(numeric_values) + 1
