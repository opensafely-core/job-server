from django.urls import reverse

from ....factories import ProjectFactory, ProjectMembershipFactory, UserFactory


def test_projectmembership_get_staff_edit_url():
    project = ProjectFactory()
    membership = ProjectMembershipFactory(project=project)

    url = membership.get_staff_edit_url()

    assert url == reverse(
        "staff:project-membership-edit",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_get_staff_remove_url():
    project = ProjectFactory()
    membership = ProjectMembershipFactory(project=project)

    url = membership.get_staff_remove_url()

    assert url == reverse(
        "staff:project-membership-remove",
        kwargs={
            "slug": project.slug,
            "pk": membership.pk,
        },
    )


def test_projectmembership_str():
    project = ProjectFactory(name="DataLab")
    user = UserFactory(username="ben")

    membership = ProjectMembershipFactory(project=project, user=user)

    assert str(membership) == "ben | DataLab"
