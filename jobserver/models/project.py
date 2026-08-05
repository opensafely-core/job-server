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


class ProjectCategory(models.TextChoices):
    """The purpose and approval process of a Project."""

    INTERNAL = "internal", "Internal platform and data development"
    """Data development and platform development activity, internally managed."""
    LEGACY = (
        "legacy",
        "Legacy COVID research activity predating specific approval processes",
    )
    """Legacy COVID research activity that came before any approval process."""
    LEGACY_APPROVED = "legacy_approved", "Legacy approved COVID research activity"
    """Legacy COVID research activity that went through the Job Server-managed
    approval process."""
    APPROVED = (
        "approved",
        "Approved research activity under the 2025 or later Directions and the NHSE-managed approval process",
    )
    """Approved research activity under the 2025 or later Directions and the
    NHSE-managed approval process"""
    UNKNOWN = "unknown", "(Unknown category)"
    """Unknown category, fallback option."""


# Patterns and compiled regex for matching different possible kinds of
# Project.number, also called identifiers.

IDENTIFIER_PATTERNS = {
    # Like INTERNAL-0123. 'INTERNAL-' followed by a string of 4 ASCII digits.
    # INTERNAL-0000 is valid but not used by convention for simplicity. Using
    # \d instead would match several other characters.
    ProjectCategory.INTERNAL: r"INTERNAL-[0-9]{4}",
    # String of ASCII digits, no leading 0. Convertible unambiguously to an int
    # and back. Using \d instead would match several other characters.
    ProjectCategory.LEGACY_APPROVED: r"[1-9][0-9]*",
    # Like POS-2026-2001. 'POS-' followed by a string of digits representing the
    # year, '-', followed by a string of digits, usually starting with 2001. Year
    # part must start '20'. Third part has no leading zero.
    ProjectCategory.APPROVED: r"POS-20[0-9]{2}-[1-9][0-9]{3}",
}
"""Dict mapping ProjectCategory to regex strings that match valid identifiers
for that category."""

IDENTIFIER_REGEXES = {
    category: re.compile(pattern) for category, pattern in IDENTIFIER_PATTERNS.items()
}
"""Dict mapping ProjectCategory to compiled regex that match valid identifiers
for that category."""

ANY_IDENTIFIER_PATTERN = r"|".join(IDENTIFIER_PATTERNS.values())
"""Regex string for any valid project identifier for some category."""
ANY_IDENTIFIER_REGEX = re.compile(ANY_IDENTIFIER_PATTERN)
"""Compiled regex for any valid project identifier for some category."""

IDENTIFIER_PATTERN_DESCRIPTION = (
    "Enter a whole number or use the format POS-20YY-NNNN (for example, POS-2026-3001)."
    "or INTERNAL-NNNN (for example, INTERNAL-0003)."
)
"""String description of how a valid project identifier may be written. For use
in forms and validation messages."""

ANY_IDENTIFIER_PATTERN_FULLMATCH = rf"^({ANY_IDENTIFIER_PATTERN})$"
"""Regex string for any valid project identifier for some category, wrapped
with ^$ anchors to require a whole match."""


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
                    number__regex=rf"^{IDENTIFIER_PATTERNS[ProjectCategory.LEGACY_APPROVED]}$",
                    then=Cast("number", IntegerField()),
                ),
                default=Value(None, output_field=IntegerField()),
                output_field=IntegerField(),
            ),
            internal_format_lex=Case(
                When(number__startswith="INTERNAL-", then=F("number")),
                default=Value("", output_field=CharField()),
                output_field=CharField(),
            ),
        ).order_by(
            "-pos_format_lex",
            F("numeric_value").desc(nulls_last=True),
            "-internal_format_lex",
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
        # Project statuses should not be shown on public-facing pages,
        # as they can be misleading.

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
        help_text="This can be found in Annex A - 1a of the NHSE Data Sharing Agreement.",
    )
    slug = models.SlugField(max_length=255, unique=True, verbose_name="URL slug")
    number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                re.compile(ANY_IDENTIFIER_PATTERN_FULLMATCH),
                IDENTIFIER_PATTERN_DESCRIPTION,
            )
        ],
        verbose_name="Project ID",
        help_text=(
            "Project ID can be found in the All Projects spreadsheet. "
            + IDENTIFIER_PATTERN_DESCRIPTION
        ),
    )
    category = models.TextField(
        choices=ProjectCategory, default=ProjectCategory.UNKNOWN, max_length=20
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

    class DataScrubbing:
        fields_to_scrub = {
            "copilot_notes": "fake copilot notes",
            "status_description": "fake status description",
        }
        allowed_fields = frozenset(
            [
                "id",
                "category",
                "copilot",
                "copilot_support_ends_at",
                "created_at",
                "created_by",
                "name",
                "number",
                "slug",
                "status",
                "updated_at",
                "updated_by",
            ]
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
                violation_error_message="Project with this Project ID already exists.",
            ),
            models.CheckConstraint(
                condition=~Q(slug=""),
                name="slug_is_not_empty",
            ),
            models.CheckConstraint(
                name="number_valid_format",
                condition=(
                    Q(number__isnull=True)
                    | Q(number__regex=ANY_IDENTIFIER_PATTERN_FULLMATCH)
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
        collaboration = (
            self.collaborations.select_related("org").order_by("-is_lead", "pk").first()
        )
        return collaboration.org if collaboration else None

    @classmethod
    def category_from_identifier(cls, identifier: str) -> ProjectCategory | None:
        """Return the ProjectCategory for which the string matches the identifier
        format or None."""
        if identifier == "":
            return ProjectCategory.UNKNOWN
        for category, pattern in IDENTIFIER_REGEXES.items():
            if pattern.fullmatch(identifier):
                return category
        return None

    @classmethod
    def is_valid_identifier(cls, identifier: str) -> bool:
        """Return True if a string matches any ProjectCategory identifier pattern."""
        return bool(cls.category_from_identifier(identifier))
