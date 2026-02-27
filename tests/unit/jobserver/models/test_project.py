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

    assert (
        project.get_approved_url()
        == "https://www.opensafely.org/approved-projects#project-42"
    )


def test_project_get_approved_url_without_number():
    project = ProjectFactory()

    assert project.get_approved_url() == "https://www.opensafely.org/approved-projects"


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


def test_next_project_identifier():
    ProjectFactory(number=100)
    ProjectFactory(number="102")
    ProjectFactory(number="103   ")

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
            ],
            [
                "third_project",
                "second_project",
                "first_project",
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
def test_apply_project_number_ordering(rows, expected):
    for row in rows:
        ProjectFactory(**row)

    ordered_projects = list(
        Project.apply_project_number_ordering().values_list("name", flat=True)
    )

    assert ordered_projects == expected


def test_apply_project_number_ordering_accepts_queryset():
    first_project = ProjectFactory(name="first_project", number="POS-2025-2001")
    second_project = ProjectFactory(name="second_project", number="7")
    ProjectFactory(name="third_project", number="POS-2026-2001")
    queryset = Project.objects.filter(pk__in=[first_project.pk, second_project.pk])

    ordered_projects = list(
        Project.apply_project_number_ordering(queryset).values_list("name", flat=True)
    )

    assert ordered_projects == ["first_project", "second_project"]
