import re

import structlog
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Case, CharField, F, IntegerField, Q, Value, When
from django.db.models.functions import Cast, Lower
from django.urls import reverse
from django.utils import functional, timezone
from django.utils.text import slugify
from furl import furl


logger = structlog.get_logger(__name__)

# Patterns, compiled regex, and validators for regex matching for different
# possible kinds of Project.number.

# Pattern for projects with an application managed in Job Server.
# String of 0-9 ASCII digits, no leading 0. Convertible unambiguously to an int
# and back. Using \d instead would match several other characters.
DIGITS_PATTERN = r"[1-9][0-9]*"
# Pattern for projects with an application managed outside of Job Server.
# Like POS-2025-2001. 'POS-' followed by a string of digits representing the
# year, '-', followed by a string of digits, usually starting with 2001. Year
# part must start '20'. Third part has no leading zero.
POS_FORMAT_PATTERN = r"POS-20[0-9]{2}-[1-9][0-9]{3}"
# Pattern for either format. This covers all valid values.
NUMBER_PATTERN = rf"{DIGITS_PATTERN}|{POS_FORMAT_PATTERN}"
NUMBER_REGEX = re.compile(NUMBER_PATTERN)
# Either format, wrapping each with ^$ anchors to require full match.
NUMBER_PATTERN_FULLMATCH = rf"^{DIGITS_PATTERN}$|^{POS_FORMAT_PATTERN}$"
NUMBER_REGEX_VALIDATOR = RegexValidator(
    re.compile(NUMBER_PATTERN_FULLMATCH),
    "Enter a whole number or use the format POS-20YY-NNNN (for example, POS-2026-2001).",
)


class ProjectQuerySet(models.QuerySet):
    def order_by_project_identifier(self):
        """
        Return projects ordered by project identifier.
        Ordering rules:
        1. POS-format identifiers sort first, in reverse lexical order.
        2. Numeric identifiers sort next, by numeric value descending.
        3. Blank or null identifiers sort last.
        4. Project name is used as a case-insensitive tie-breaker.
        """
        return self.annotate(
            pos_format_lex=Case(
                When(number__startswith="POS-", then=F("number")),
                default=Value("", output_field=CharField()),
                output_field=CharField(),
            ),
            numeric_value=Case(
                When(
                    number__regex=rf"^{DIGITS_PATTERN}$",
                    then=Cast("number", IntegerField()),
                ),
                default=Value(None, output_field=IntegerField()),
                output_field=IntegerField(),
            ),
        ).order_by(
            "-pos_format_lex",
            F("numeric_value").desc(nulls_last=True),
            Lower("name"),
        )


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
        verbose_name="Project Co-pilot",
        help_text="Ask the BI Co-pilot Lead to find out who is Co-piloting this new project.",
    )

    orgs = models.ManyToManyField(
        "Org",
        related_name="projects",
        through="ProjectCollaboration",
        verbose_name="Link project to an organisation",
        help_text="This is the sponsoring organisation, found in Section 9 of the NHSE OpenSAFELY Project Application form.",
    )

    name = models.TextField(
        unique=True,
        verbose_name="Project title",
        help_text="This can be found in Section 7 of the NHSE OpenSAFELY Project Application form.",
    )
    slug = models.SlugField(max_length=255, unique=True, verbose_name="URL slug")
    number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[NUMBER_REGEX_VALIDATOR],
        verbose_name="Project ID",
        help_text="Project ID can be found in the All Projects spreadsheet.",
    )

    copilot_support_ends_at = models.DateTimeField(null=True, blank=True)

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

    objects = ProjectQuerySet.as_manager()

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
            models.CheckConstraint(
                name="number_valid_format",
                condition=(
                    Q(number__isnull=True) | Q(number__regex=NUMBER_PATTERN_FULLMATCH)
                ),
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
        if self.number:
            return furl(f"https://www.opensafely.org/project/{self.number}/")

        return "https://www.opensafely.org/projects/not-found/"

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
        if self.number is None:
            return self.name

        return f"{self.number} - {self.name}"

    @functional.cached_property
    def org(self):
        return self.orgs.filter(collaborations__is_lead=True).first()

    @classmethod
    def next_project_identifier(cls):
        """
        Return the next numeric project number, or 1 if no numeric values exist.
        """
        numeric_values = [
            int(number)
            for number in cls.objects.values_list("number", flat=True)
            if number is not None and number.isdigit()
        ]

        if not numeric_values:
            return 1

        return max(numeric_values) + 1
