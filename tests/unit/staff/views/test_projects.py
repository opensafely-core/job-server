import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404

from applications.models import Application
from jobserver.authorization import ProjectCollaborator, ProjectDeveloper
from jobserver.commands import project_members
from jobserver.models import Project
from jobserver.utils import dotted_path, set_from_qs
from staff.views.projects import (
    ProjectAddMember,
    ProjectAuditLog,
    ProjectDetail,
    ProjectEdit,
    ProjectLinkApplication,
    ProjectList,
    ProjectMembershipEdit,
    ProjectMembershipRemove,
)

from ....factories import (
    ApplicationFactory,
    OrgFactory,
    ProjectFactory,
    UserFactory,
)


def test_projectaddmember_get_success(rf, staff_area_administrator):
    project = ProjectFactory()
    UserFactory(username="beng", fullname="Ben Goldacre")

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectAddMember.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert response.context_data["project"] == project
    assert "Ben Goldacre (beng)" in response.rendered_content


def test_projectaddmember_post_success(rf, staff_area_administrator):
    project = ProjectFactory()
    user1 = UserFactory()
    user2 = UserFactory()

    data = {
        "roles": ["jobserver.authorization.roles.ProjectDeveloper"],
        "users": [user1.pk, user2.pk],
    }
    request = rf.post("/", data)
    request.user = staff_area_administrator

    response = ProjectAddMember.as_view()(request, slug=project.slug)

    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    assert set_from_qs(project.members.all()) == {user1.pk, user2.pk}

    assert project.memberships.filter(roles=[ProjectDeveloper]).count() == 2


def test_projectaddmember_unauthorized(rf, staff_area_administrator):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectAddMember.as_view()(request)


def test_projectaddmember_unknown_project(rf, staff_area_administrator):
    request = rf.post("/")
    request.user = staff_area_administrator

    with pytest.raises(Http404):
        ProjectAddMember.as_view()(request, slug="test")


def test_projectauditlog_filter_by_type(
    rf, staff_area_administrator, project_membership
):
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
        roles=[ProjectCollaborator],
        by=actor,
    )
    project_members.update_roles(
        membership=project.memberships.first(),
        by=actor,
        roles=[ProjectCollaborator, ProjectDeveloper],
    )

    request = rf.get("/?types=project_member_added")
    request.user = staff_area_administrator

    response = ProjectAuditLog.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert len(response.context_data["events"]) == 1
    assert response.context_data["events"][0].context["actor"].display_value == str(
        actor
    )


def test_projectauditlog_success(rf, staff_area_administrator, project_membership):
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
        roles=[ProjectCollaborator],
        by=actor,
    )
    project_members.update_roles(
        membership=project.memberships.first(),
        by=actor,
        roles=[ProjectCollaborator, ProjectDeveloper],
    )

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectAuditLog.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert len(response.context_data["events"]) == 3
    assert response.context_data["project"] == project


def test_projectauditlog_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectAuditLog.as_view()(request, slug=project.slug)


def test_projectauditlog_num_queries(
    rf, django_assert_num_queries, staff_area_administrator, project_membership
):
    project = ProjectFactory()
    project_membership(
        project=project,
        user=UserFactory(),
        roles=[ProjectCollaborator],
        by=UserFactory(),
    )
    project_members.update_roles(
        membership=project.memberships.first(),
        by=UserFactory(),
        roles=[ProjectCollaborator, ProjectDeveloper],
    )

    request = rf.get("/")
    request.user = staff_area_administrator

    with django_assert_num_queries(11):
        response = ProjectAuditLog.as_view()(request, slug=project.slug)
        assert response.status_code == 200

    with django_assert_num_queries(2):
        response.render()


def test_projectauditlog_unknown_project(rf, staff_area_administrator):
    request = rf.get("/")
    request.user = staff_area_administrator

    with pytest.raises(Http404):
        ProjectAuditLog.as_view()(request, slug="")


def test_projectdetail_success(rf, staff_area_administrator):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectDetail.as_view()(request, slug=project.slug)

    assert response.status_code == 200

    expected = set_from_qs(project.workspaces.all())
    output = set_from_qs(response.context_data["workspaces"])
    assert output == expected


def test_projectedit_get_success(rf, staff_area_administrator):
    project = ProjectFactory(orgs=[OrgFactory()])

    UserFactory(username="beng", fullname="Ben Goldacre")

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert "Ben Goldacre (beng)" in response.rendered_content


def test_projectedit_get_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectedit_post_success(rf, staff_area_administrator):
    project = ProjectFactory(name="test", number=123, orgs=[OrgFactory()])
    old_project_url = project.get_absolute_url()

    new_copilot = UserFactory()
    new_org = OrgFactory()

    data = {
        "name": "New Name",
        "slug": "new-name",
        "number": 456,
        "copilot": str(new_copilot.pk),
        "copilot_support_ends_at": "",
        "orgs": [str(new_org.pk)],
        "status": Project.Statuses.COMPLETED_AWAITING,
        "status_description": "",
    }
    request = rf.post("/", data)
    request.user = staff_area_administrator

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors

    project.refresh_from_db()
    assert response.url == project.get_staff_url()
    assert project.name == "New Name"
    assert project.slug == "new-name"
    assert project.number == 456
    assert project.copilot == new_copilot
    assert set_from_qs(project.orgs.all()) == {new_org.pk}
    assert project.updated_by == staff_area_administrator
    assert project.redirects.count() == 1
    assert project.redirects.first().old_url == old_project_url


def test_projectedit_post_success_when_not_changing_slug(rf, staff_area_administrator):
    org = OrgFactory()
    project = ProjectFactory(name="Test", slug="test", number=123, orgs=[org])

    new_copilot = UserFactory()

    data = {
        "name": "Test",
        "slug": "test",
        "number": 456,
        "copilot": str(new_copilot.pk),
        "copilot_support_ends_at": "",
        "orgs": str(org.pk),
        "status": Project.Statuses.POSTPONED,
        "status_description": "",
    }
    request = rf.post("/", data)
    request.user = staff_area_administrator

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors

    project.refresh_from_db()
    assert response.url == project.get_staff_url()
    assert project.name == "Test"
    assert project.slug == "test"
    assert project.number == 456
    assert project.copilot == new_copilot
    assert project.redirects.count() == 0


def test_projectedit_post_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectedit_post_unknown_project(rf, staff_area_administrator):
    request = rf.post("/")
    request.user = staff_area_administrator

    with pytest.raises(Http404):
        ProjectEdit.as_view()(request, slug="")


def test_projectlinkapplication_get_empty_application_list(
    rf, staff_area_administrator
):
    ApplicationFactory(status=Application.Statuses.ONGOING)
    ApplicationFactory(status=Application.Statuses.REJECTED)

    project = ProjectFactory()

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectLinkApplication.as_view()(request, slug=project.slug)

    assert response.status_code == 200

    assert not response.context_data["applications"]


def test_projectlinkapplication_get_success(rf, staff_area_administrator):
    approved_fully = ApplicationFactory(
        project=None,
        status=Application.Statuses.APPROVED_FULLY,
    )
    approved_subject_to = ApplicationFactory(
        project=None,
        status=Application.Statuses.APPROVED_SUBJECT_TO,
    )
    completed = ApplicationFactory(
        project=None,
        status=Application.Statuses.COMPLETED,
    )
    ApplicationFactory(
        project=None,
        status=Application.Statuses.ONGOING,
    )
    ApplicationFactory(
        project=None,
        status=Application.Statuses.REJECTED,
    )

    project = ProjectFactory()

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectLinkApplication.as_view()(request, slug=project.slug)

    assert response.status_code == 200

    applications = response.context_data["applications"]
    assert len(applications) == 3

    assert set(applications) == {approved_fully, approved_subject_to, completed}


def test_projectlinkapplication_post_success(rf, staff_area_administrator):
    application = ApplicationFactory(
        project=None,
        status=Application.Statuses.COMPLETED,
    )
    project = ProjectFactory()

    request = rf.post("/", {"application": application.pk})
    request.user = staff_area_administrator

    response = ProjectLinkApplication.as_view()(request, slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == project.get_staff_url()

    application.refresh_from_db()
    assert application.project == project


def test_projectlinkapplication_post_unknown_application(rf, staff_area_administrator):
    project = ProjectFactory()

    request = rf.post("/", {"application": "0"})
    request.user = staff_area_administrator

    response = ProjectLinkApplication.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert response.context_data["form"].errors == {
        "application": ["Unknown Application"]
    }


def test_projectlinkapplication_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectLinkApplication.as_view()(request, slug=project.slug)


def test_projectlinkapplication_unknown_project(rf, staff_area_administrator):
    request = rf.get("/")
    request.user = staff_area_administrator

    with pytest.raises(Http404):
        ProjectLinkApplication.as_view()(request, slug="")


def test_projectlist_filter_by_org(rf, staff_area_administrator):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    ProjectFactory.create_batch(2)

    request = rf.get(f"/?orgs={org.slug}")
    request.user = staff_area_administrator

    response = ProjectList.as_view()(request)

    assert set_from_qs(response.context_data["project_list"]) == {project.pk}


def test_projectlist_find_by_username(rf, staff_area_administrator):
    ProjectFactory(name="ben")
    ProjectFactory(name="benjamin")
    ProjectFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = staff_area_administrator

    response = ProjectList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["project_list"]) == 2


def test_projectlist_success(rf, staff_area_administrator):
    ProjectFactory.create_batch(5)

    request = rf.get("/")
    request.user = staff_area_administrator

    response = ProjectList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["project_list"])


def test_projectlist_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectList.as_view()(request, project_slug=project.slug)


@pytest.mark.parametrize("next_url", ["", "/some/other/url/"])
def test_projectmembershipedit_success(
    rf, staff_area_administrator, next_url, project_membership
):
    project = ProjectFactory()
    user = UserFactory()

    project_membership(project=project, user=user, roles=[ProjectCollaborator])

    membership = project_membership(project=project, user=UserFactory())

    suffix = f"?next={next_url}" if next_url else ""
    request = rf.post(f"/{suffix}", {"roles": [dotted_path(ProjectDeveloper)]})
    request.user = staff_area_administrator

    response = ProjectMembershipEdit.as_view()(
        request, slug=project.slug, pk=membership.pk
    )

    assert response.status_code == 302

    expected = next_url if next_url else project.get_staff_url()
    assert response.url == expected

    membership.refresh_from_db()
    assert membership.roles == [ProjectDeveloper]


def test_projectmembershipedit_unknown_membership(
    rf, staff_area_administrator, project_membership
):
    project = ProjectFactory()

    project_membership(project=project, user=UserFactory())

    request = rf.get("/")
    request.user = staff_area_administrator

    with pytest.raises(Http404):
        ProjectMembershipEdit.as_view()(request, slug=project.slug, pk="0")


def test_projectmembershipedit_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectMembershipEdit.as_view()(request)


@pytest.mark.parametrize("next_url", ["", "/some/other/url/"])
def test_projectmembershipremove_success(
    rf, staff_area_administrator, next_url, project_membership
):
    project = ProjectFactory()
    user = UserFactory()

    membership = project_membership(project=project, user=user)

    suffix = f"?next={next_url}" if next_url else ""
    request = rf.post(f"/{suffix}")
    request.user = staff_area_administrator

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectMembershipRemove.as_view()(
        request, slug=project.slug, pk=membership.pk
    )

    assert response.status_code == 302

    expected = next_url if next_url else project.get_staff_url()
    assert response.url == expected

    project.refresh_from_db()
    assert user not in project.members.all()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == f"Removed {user.username} from {project.title}"


def test_projectmembershipremove_unauthorized(rf, project_membership):
    membership = project_membership()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectMembershipRemove.as_view()(
            request, slug=membership.project.slug, pk=membership.pk
        )


def test_projectmembershipremove_unknown_membership(rf, staff_area_administrator):
    project = ProjectFactory()

    assert project.memberships.count() == 0

    request = rf.post("/")
    request.user = staff_area_administrator

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    with pytest.raises(Http404):
        ProjectMembershipRemove.as_view()(request, slug=project.slug, pk=0)
