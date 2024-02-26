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


@pytest.mark.django_db(transaction=True)
def test_project_constraints_created_at_and_created_by_only_one_set():
    with pytest.raises(IntegrityError):
        ProjectFactory(created_at=timezone.now(), created_by=None)

    with pytest.raises(IntegrityError):
        ProjectFactory(created_at=None, created_by=UserFactory())


def test_project_constraints_updated_at_and_updated_by_both_set():
    ProjectFactory(updated_at=timezone.now(), updated_by=UserFactory())


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


def test_project_get_reports_url():
    project = ProjectFactory()

    url = project.get_reports_url()

    assert url == reverse(
        "project-report-list",
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
