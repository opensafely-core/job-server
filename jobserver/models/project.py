import structlog
from django.db import models
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.functions import Cast, Lower, Substr
from django.urls import reverse
from django.utils import functional, timezone
from django.utils.text import slugify
from furl import furl


logger = structlog.get_logger(__name__)
ALPHANUMERIC_IDENTIFIER_REGEX = r"^POS-20\d{2}-\d{4,}$"
NUMERIC_IDENTIFIER_REGEX = r"^\d+$"


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
    number = models.CharField(max_length=20, null=True, blank=True)

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
        This handles both int values and digit-only strings so it remains valid
        when number is migrated from IntegerField to CharField.
        """
        numeric_values = [
            int(str(value).strip())
            for value in cls.objects.values_list("number", flat=True)
            if value is not None and str(value).strip().isdigit()
        ]

        if not numeric_values:
            return 1

        return max(numeric_values) + 1

    @classmethod
    def apply_project_number_ordering(cls, queryset=None):
        """
        Return a queryset ordered by project number in custom order.
        Ordering rules:
        1. Alphanumeric identifiers (e.g. POS-2025-2001) first, newest first
        by year segment, then sequence segment.
        2. Numeric identifiers next, highest numeric value first.
        3. Missing identifiers (NULL/blank) last.
        4. Project name (case-insensitive) as a final tie-breaker.
        """
        qs = cls.objects.all() if queryset is None else queryset

        # Classify each project number into cases to allow ordering:
        # 0 = POS-style identifier, 1 = numeric identifier, 2 = missing/default.
        qs = qs.annotate(
            number_type=Case(
                When(number__regex=ALPHANUMERIC_IDENTIFIER_REGEX, then=Value(0)),
                When(number__regex=NUMERIC_IDENTIFIER_REGEX, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )

        # For alphanumeric identifiers(e.g.POS-2025-2001), extract the year segment(2025)
        # and cast it to integer so we can sort by year numerically.
        qs = qs.annotate(
            year=Case(
                When(
                    number__regex=ALPHANUMERIC_IDENTIFIER_REGEX,
                    then=Cast(Substr("number", 5, 4), IntegerField()),
                ),
                default=Value(None, output_field=IntegerField()),
                output_field=IntegerField(),
            )
        )

        # For alphanumeric identifiers(e.g.POS-2025-2001), extract the sequence segment(2001)
        #  and cast it to integer so we can sort by sequence numerically.
        qs = qs.annotate(
            sequence=Case(
                When(
                    number__regex=ALPHANUMERIC_IDENTIFIER_REGEX,
                    then=Cast(Substr("number", 10), IntegerField()),
                ),
                default=Value(None, output_field=IntegerField()),
                output_field=IntegerField(),
            )
        )

        # For numeric identifiers(e.g "123"), cast the number to integer so we can sort
        # numerically instead of lexically.
        qs = qs.annotate(
            numeric_value=Case(
                When(
                    number__regex=NUMERIC_IDENTIFIER_REGEX,
                    then=Cast("number", IntegerField()),
                ),
                default=Value(None, output_field=IntegerField()),
                output_field=IntegerField(),
            )
        )

        qs = qs.order_by(
            "number_type",
            "-year",
            "-sequence",
            "-numeric_value",
            Lower("name"),
        )

        return qs
