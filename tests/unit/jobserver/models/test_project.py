import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Project

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
        pytest.param("POS-2026-2001", id="format-typical"),
        pytest.param("POS-2099-9999", id="format-max"),
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
        # POS-Format Identifiers
        # Format errors - wrong structure
        pytest.param("PO-2026-2001", id="first-part-too-short"),
        pytest.param("POST-2026-2001", id="first-part-too-long"),
        pytest.param("POS-202-2000", id="second-part-too-short"),
        pytest.param("POS-20260-2000", id="second-part-too-long"),
        pytest.param("POS-2026-200", id="third-part-too-short"),
        pytest.param("POS-2026-20000", id="third-part-too-long"),
        pytest.param("POS-", id="missing-second-and-third-parts"),
        pytest.param("POS-9001", id="missing-third-part"),
        pytest.param("POS-2001-", id="empty-third-part"),
        pytest.param("POS-2026-2000-2001", id="four-parts"),
        pytest.param("pos-2026-2001", id="lowercase"),
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
        # Leading or trailing whitespace of otherwise valid values
        pytest.param(" POS-2026-2001", id="identifier-leading-whitespace"),
        pytest.param("POS-2026-2001 ", id="identifier-trailing-whitespace"),
        pytest.param(" POS-2026-2001 ", id="identifier-both-whitespace"),
        pytest.param(" 123", id="int-leading-whitespace"),
        pytest.param("123 ", id="int-trailing-whitespace"),
        pytest.param(" 123 ", id="int-both-whitespace"),
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


def test_next_project_identifier():
    ProjectFactory(number="100")
    ProjectFactory(number="102")
    ProjectFactory(number="103")

    assert Project.next_project_identifier() == 104


def test_next_project_identifier_returns_one_when_no_numeric_ids_exist():
    ProjectFactory(number=None)

    assert Project.next_project_identifier() == 1


@pytest.mark.parametrize(
    "rows,expected",
    [
        (
            [
                {"name": "first_project", "number": "POS-2024-2009"},
                {"name": "second_project", "number": "POS-2025-2001"},
                {"name": "third_project", "number": "POS-2025-2003"},
                {"name": "fourth_project", "number": "7"},
                {"name": "fifth_project", "number": "42"},
                {"name": "sixth_project", "number": None},
                {"name": "seventh_project", "number": "POS-2023-2009"},
            ],
            [
                "third_project",
                "second_project",
                "first_project",
                "seventh_project",
                "fifth_project",
                "fourth_project",
                "sixth_project",
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
