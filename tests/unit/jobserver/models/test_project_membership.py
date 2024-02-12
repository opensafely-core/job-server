import pytest
from django.urls import reverse

from jobserver.models import ProjectMembership

from ....factories import ProjectFactory, UserFactory


def test_projectmembership_direct_use_of_create():
    with pytest.raises(TypeError):
        ProjectMembership.objects.create()


def test_projectmembership_direct_use_of_update():
    with pytest.raises(TypeError):
        ProjectMembership.objects.update()


def test_projectmembership_get_staff_edit_url(project_membership):
    project = ProjectFactory()
    membership = project_membership(project=project)

    url = membership.get_staff_edit_url()

    assert url == reverse(
        "staff:project-membership-edit",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_get_staff_remove_url(project_membership):
    project = ProjectFactory()
    membership = project_membership(project=project)

    url = membership.get_staff_remove_url()

    assert url == reverse(
        "staff:project-membership-remove",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_str(project_membership):
    project = ProjectFactory(name="DataLab")
    user = UserFactory(username="ben")

    membership = project_membership(project=project, user=user)

    assert str(membership) == "ben | DataLab"
