import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Project, ProjectCategory

from ....factories import (
    OrgFactory,
    ProjectCollaborationFactory,
    ProjectFactory,
    UserFactory,
)


def test_project_constraints_created_at_and_created_by_both_set():
    ProjectFactory(created_at=timezone.now(), created_by=UserFactory())


@pytest.mark.slow_test
@pytest.mark.django_db(transaction=True)
def test_project_constraints_created_at_and_created_by_only_one_set():
    with pytest.raises(IntegrityError):
        ProjectFactory(created_at=timezone.now(), created_by=None)

    with pytest.raises(IntegrityError):
        ProjectFactory(created_at=None, created_by=UserFactory())


def test_project_constraints_updated_at_and_updated_by_both_set():
    ProjectFactory(updated_at=timezone.now(), updated_by=UserFactory())


@pytest.mark.slow_test
@pytest.mark.django_db(transaction=True)
def test_project_constraints_updated_at_and_updated_by_only_one_set():
    with pytest.raises(IntegrityError):
        ProjectFactory(updated_at=timezone.now(), updated_by=None)

    ProjectFactory(updated_by=UserFactory())
    with pytest.raises(IntegrityError):
        # use update here because auto_now doesn't apply to this type of query
        Project.objects.update(updated_at=None)


@pytest.mark.parametrize(
    "number",
    [
        pytest.param(None, id="null"),
        pytest.param("1", id="digit-1"),
        pytest.param("123", id="multi-digit"),
        pytest.param("99999999", id="long-digit"),
        pytest.param("POS-2000-1000", id="format-min-year"),
        pytest.param("POS-2026-3001", id="format-typical"),
        pytest.param("POS-2099-9999", id="format-max"),
        pytest.param("INTERNAL-0000", id="internal-format-0digits"),
        pytest.param("INTERNAL-0001", id="internal-format-1digits"),
        pytest.param("INTERNAL-0023", id="internal-format-2digits"),
        pytest.param("INTERNAL-0456", id="internal-format-3digits"),
        pytest.param("INTERNAL-9870", id="internal-format-4digits"),
    ],
)
def test_project_constraints_number_valid(number):
    """Valid project numbers can be saved in the database."""
    project = ProjectFactory(number=number)
    assert project.pk is not None
    assert project.number == number


@pytest.mark.parametrize(
    "number",
    [
        # Null is allowed, the empty string is not
        pytest.param("", id="empty-string"),
        # Problematic characters
        pytest.param(" ", id="space-character"),
        pytest.param("   ", id="three-space-characters"),
        pytest.param(" " * 1000, id="thousand-space-characters"),
        pytest.param("\n", id="new-line"),
        pytest.param("!@#^%$&*;,.'`|~", id="punctuation"),
        pytest.param("\u2728 hello \U0001f338 world \U0001f40d", id="unicode"),
        # Integer identifiers
        # Leading zeroes
        pytest.param("0", id="single-0"),
        pytest.param("0001", id="leading-0s"),
        # Negative numbers
        pytest.param("-0", id="negative-zero"),
        pytest.param("-1", id="negative-one"),
        pytest.param("-123", id="negative-number"),
        pytest.param("-", id="just-dash"),
        # Non-integers
        pytest.param("1.5", id="fractional"),
        pytest.param("one", id="word"),
        pytest.param("abc", id="letters"),
        pytest.param("project number", id="phrase"),
        pytest.param("bad-project-id", id="three-words-with-dashes"),
        pytest.param("!", id="punctuation-mark"),
        pytest.param("１２３", id="just-digits-with-spaces"),
        # POS-Format Identifiers
        # Format errors - wrong structure
        pytest.param("PO-2026-2001", id="first-part-too-short"),
        pytest.param("POST-2026-2001", id="first-part-too-long"),
        pytest.param("POS-202-2000", id="second-part-too-short"),
        pytest.param("POS-20260-2000", id="second-part-too-long"),
        pytest.param("POS-2026-300", id="third-part-too-short"),
        pytest.param("POS-2026-30000", id="third-part-too-long"),
        pytest.param("POS-", id="missing-second-and-third-parts"),
        pytest.param("POS-9001", id="missing-third-part"),
        pytest.param("POS-2001-", id="empty-third-part"),
        pytest.param("POS-2026-3000-2001", id="four-parts"),
        pytest.param("pos-2026-2001", id="pos-lowercase"),
        pytest.param("Pos-2026-3001", id="pos-title-case"),
        pytest.param("-POS-2026-3001", id="pos-leading-delimiter"),
        pytest.param("POS-2026-3001-", id="pos-trailing-delimiter"),
        pytest.param("POS–2026-3001", id="pos-en-dash-delimiter"),
        pytest.param("POS—2026-3001", id="pos-em-dash-delimiter"),
        pytest.param("POS−2026-3001", id="pos-minus-sign-delimiter"),
        pytest.param("POS -2026-3001", id="pos-space-before-delimiter"),
        pytest.param("POS- 2026-3001", id="pos-space-after-delimiter"),
        pytest.param("POS - 2026-3001", id="pos-spaces-around-delimiter"),
        # Format errors - wrong delimiter
        pytest.param("POS_2026-2001", id="underscore-first"),
        pytest.param("POS-2026_2001", id="underscore-second"),
        # Format errors - invalid values - first part
        # The first in this section is like an application identifier.
        pytest.param("AOS-2026-2001", id="first-part-wrong-first-char"),
        pytest.param("P0S-2026-2001", id="first-part-zero-instead-O"),
        pytest.param("POG-2026-2001", id="first-part-wrong-third-char"),
        pytest.param("2026-2001", id="first-part-no-prefix"),
        # Format errors - invalid values - second part
        pytest.param("POS-3001-2000", id="second-part-starts-with-3"),
        pytest.param("POS-1999-2000", id="second-part-starts-with-1"),
        pytest.param("POS-0999-0000", id="second-part-starts-with-0"),
        pytest.param("POS-a999-0000", id="second-part-starts-with-a"),
        # Format errors - invalid values - third part
        pytest.param("POS-2001-0000", id="third-part-starts-with-0"),
        pytest.param("POS-2001-a000", id="third-part-starts-with-a"),
        # INTERNAL-Format
        # Format errors - wrong structure
        pytest.param("INTERNAL0001", id="internal-no-delimiter"),
        pytest.param("INTERNAL--0001", id="internal-two-delimiters"),
        pytest.param("INTERNAL_0001", id="internal-underscore-delimiter"),
        pytest.param("INTERNAL 0001", id="internal-space-delimiter"),
        pytest.param("I-0001", id="internal-short-prefix"),
        pytest.param("INT-0001", id="internal-short-prefix2"),
        pytest.param("internal-0001", id="internal-lowercase"),
        pytest.param("Internal-0001", id="internal-title-case"),
        pytest.param("-INTERNAL-0001", id="internal-leading-delimiter"),
        pytest.param("INTERNAL-0001-", id="internal-trailing-delimiter"),
        pytest.param("INTERNAL–0001", id="internal-en-dash-delimiter"),
        pytest.param("INTERNAL—0001", id="internal-em-dash-delimiter"),
        pytest.param("INTERNAL−0001", id="internal-minus-sign-delimiter"),
        pytest.param("INTERNAL -0001", id="internal-space-before-delimiter"),
        pytest.param("INTERNAL- 0001", id="internal-space-after-delimiter"),
        pytest.param("INTERNAL - 0001", id="internal-spaces-around-delimiter"),
        # Format errors - wrong int part
        pytest.param("INTERNAL-1.255", id="internal-decimal"),
        pytest.param("INTERNAL-1.25", id="internal-decimal2"),
        pytest.param("INTERNAL-6", id="internal-0-leading-zero"),
        pytest.param("INTERNAL-09", id="internal-1-leading-zero"),
        pytest.param("INTERNAL-005", id="internal-2-leading-zero"),
        pytest.param("INTERNAL-00007", id="internal-4-leading-zero"),
        pytest.param("INTERNAL-012", id="internal-1-leading-zero"),
        pytest.param("INTERNAL-a", id="internal-letter"),
        pytest.param("INTERNAL-project", id="internal-word"),
        pytest.param("INTERNAL-PROJECT", id="internal-word2"),
        pytest.param("INTERNAL-@", id="internal-punctuation"),
        # Leading or trailing whitespace of otherwise valid values
        pytest.param(" POS-2026-3001", id="identifier-leading-whitespace"),
        pytest.param("POS-2026-3001 ", id="identifier-trailing-whitespace"),
        pytest.param(" POS-2026-3001 ", id="identifier-both-whitespace"),
        pytest.param(" 123", id="int-leading-whitespace"),
        pytest.param("123 ", id="int-trailing-whitespace"),
        pytest.param(" 123 ", id="int-both-whitespace"),
        pytest.param(" INTERNAL-0123", id="internal-leading-whitespace"),
        pytest.param("INTERNAL-0123 ", id="internal-trailing-whitespace"),
        pytest.param(" INTERNAL-0123 ", id="internal-both-whitespace"),
    ],
)
def test_project_constraints_number_invalid(number):
    """Invalid project numbers raise IntegrityError."""
    with pytest.raises(IntegrityError):
        ProjectFactory(number=number)


def test_project_get_absolute_url():
    project = ProjectFactory()

    url = project.get_absolute_url()

    assert url == reverse(
        "project-detail",
        kwargs={
            "project_slug": project.slug,
        },
    )


def test_project_get_approved_url_with_number():
    project = ProjectFactory(number=42)

    assert str(project.get_approved_url()) == "https://www.opensafely.org/project/42/"


def test_project_get_approved_url_without_number():
    project = ProjectFactory()

    assert (
        project.get_approved_url() == "https://www.opensafely.org/projects/not-found/"
    )


def test_project_get_edit_url():
    project = ProjectFactory()

    url = project.get_edit_url()

    assert url == reverse(
        "project-edit",
        kwargs={
            "project_slug": project.slug,
        },
    )


def test_project_get_logs_url():
    project = ProjectFactory()

    url = project.get_logs_url()

    assert url == reverse(
        "project-event-log",
        kwargs={
            "project_slug": project.slug,
        },
    )


def test_project_get_releases_url():
    project = ProjectFactory()

    url = project.get_releases_url()

    assert url == reverse(
        "project-release-list",
        kwargs={
            "project_slug": project.slug,
        },
    )


def test_project_get_staff_url():
    project = ProjectFactory()

    url = project.get_staff_url()

    assert url == reverse("staff:project-detail", kwargs={"slug": project.slug})


def test_project_staff_audit_url():
    project = ProjectFactory()

    url = project.get_staff_audit_url()

    assert url == reverse("staff:project-audit-log", kwargs={"slug": project.slug})


def test_project_get_staff_edit_url():
    project = ProjectFactory()

    url = project.get_staff_edit_url()

    assert url == reverse("staff:project-edit", kwargs={"slug": project.slug})


def test_project_populates_slug():
    assert ProjectFactory(name="Test Project", slug="").slug == "test-project"


def test_project_str():
    project = ProjectFactory(name="Very Good Project")
    assert str(project) == "Very Good Project"

    project = ProjectFactory(name="Another Very Good Project", number=42)
    assert str(project) == "42 - Another Very Good Project"


def test_project_title():
    project = ProjectFactory(number=None)
    assert project.title == project.name

    project = ProjectFactory(name="test", number=123)
    assert project.title == "123 - test"


def test_project_org():
    project = ProjectFactory()
    ProjectCollaborationFactory(org=OrgFactory(), project=project, is_lead=False)
    lead_org = OrgFactory()
    ProjectCollaborationFactory(org=lead_org, project=project, is_lead=True)
    assert project.org == lead_org


def test_project_org_returns_first_org_when_no_lead():
    project = ProjectFactory()
    first_org = OrgFactory()
    second_org = OrgFactory()
    ProjectCollaborationFactory(org=first_org, project=project, is_lead=False)
    ProjectCollaborationFactory(org=second_org, project=project, is_lead=False)

    assert project.org == first_org


@pytest.mark.parametrize(
    "rows,expected",
    [
        (
            [
                {"name": "project_1", "number": "POS-2024-2009"},
                {"name": "project_2", "number": "POS-2025-2001"},
                {"name": "project_3", "number": "POS-2025-2003"},
                {"name": "project_4", "number": "7"},
                {"name": "project_5", "number": "42"},
                {"name": "project_6", "number": None},
                {"name": "project_9", "number": "INTERNAL-0001"},
                {"name": "project_8", "number": "POS-2023-2009"},
                {"name": "project_7", "number": "INTERNAL-0123"},
            ],
            [
                "project_3",
                "project_2",
                "project_1",
                "project_8",
                "project_5",
                "project_4",
                "project_7",
                "project_9",
                "project_6",
            ],
        ),
        (
            [
                {"name": "first_project", "number": "2"},
                {"name": "second_project", "number": "10"},
                {"name": "third_project", "number": "100"},
            ],
            ["third_project", "second_project", "first_project"],
        ),
        (
            [
                {"name": "second_project", "number": None},
                {"name": "first_project", "number": None},
            ],
            ["first_project", "second_project"],
        ),
    ],
)
def test_order_by_project_identifier(rows, expected):
    for row in rows:
        ProjectFactory(**row)

    ordered_projects = list(
        Project.objects.all()
        .order_by_project_identifier()
        .values_list("name", flat=True)
    )

    assert ordered_projects == expected


@pytest.mark.parametrize(
    "identifier,expected_category,expected_bool",
    [
        ("INTERNAL-0123", ProjectCategory.INTERNAL, True),
        ("123", ProjectCategory.LEGACY_APPROVED, True),
        ("POS-2026-2001", ProjectCategory.APPROVED, True),
        ("", ProjectCategory.UNKNOWN, True),
        ("bad identifier", None, False),
    ],
)
def test_category_from_identifier_methods(identifier, expected_category, expected_bool):
    """Test that Project classmethods category_from_identifier and
    is_valid_identifier return expected values."""
    # is_valid_identifier is a readability wrapper for category_from_identifier.
    # They are so closely linked it makes more sense to test them in one test.
    assert Project.category_from_identifier(identifier) == expected_category
    assert Project.is_valid_identifier(identifier) == expected_bool
