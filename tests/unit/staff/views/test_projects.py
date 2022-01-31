import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.authorization import ProjectCoordinator, ProjectDeveloper
from jobserver.models import Project
from jobserver.utils import dotted_path, set_from_qs
from staff.views.projects import (
    ProjectAddMember,
    ProjectCreate,
    ProjectDetail,
    ProjectEdit,
    ProjectList,
    ProjectMembershipEdit,
    ProjectMembershipRemove,
)

from ....factories import (
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
)


def test_projectaddmember_get_success(rf, core_developer):
    project = ProjectFactory()
    UserFactory(username="beng", first_name="Ben", last_name="Goldacre")

    request = rf.get("/")
    request.user = core_developer

    response = ProjectAddMember.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert response.context_data["project"] == project
    assert "beng (Ben Goldacre)" in response.rendered_content


def test_projectaddmember_post_success(rf, core_developer):
    project = ProjectFactory()
    user1 = UserFactory()
    user2 = UserFactory()

    data = {
        "roles": ["jobserver.authorization.roles.ProjectDeveloper"],
        "users": [user1.pk, user2.pk],
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ProjectAddMember.as_view()(request, slug=project.slug)

    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    assert set_from_qs(project.members.all()) == {user1.pk, user2.pk}

    assert project.memberships.filter(roles=[ProjectDeveloper]).count() == 2


def test_projectaddmember_unauthorized(rf, core_developer):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectAddMember.as_view()(request)


def test_projectaddmember_unknown_project(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ProjectAddMember.as_view()(request, slug="test")


def test_projectcreate_post_success(rf, core_developer):
    org = OrgFactory()

    assert not Project.objects.exists()

    data = {
        "name": "new-name",
        "org": org.pk,
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ProjectCreate.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors

    project = Project.objects.first()
    assert response.url == project.get_staff_url()
    assert project.created_by == core_developer
    assert project.name == "new-name"
    assert project.org == org


def test_projectcreate_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectCreate.as_view()(request)


def test_projectdetail_success(rf, core_developer):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ProjectDetail.as_view()(request, slug=project.slug)

    assert response.status_code == 200

    expected = set_from_qs(project.workspaces.all())
    output = set_from_qs(response.context_data["workspaces"])
    assert output == expected


def test_projectedit_get_success(rf, core_developer):
    project = ProjectFactory()

    UserFactory(username="beng", first_name="Ben", last_name="Goldacre")

    request = rf.get("/")
    request.user = core_developer

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 200
    assert "beng (Ben Goldacre)" in response.rendered_content


def test_projectedit_get_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectedit_post_success(rf, core_developer):
    project = ProjectFactory()

    new_copilot = UserFactory()

    data = {
        "name": "new-name",
        "copilot": str(new_copilot.pk),
        "copilot_support_ends_at": "",
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == project.get_staff_url()

    project.refresh_from_db()
    assert project.name == "new-name"
    assert project.copilot == new_copilot


def test_projectedit_post_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectlist_filter_by_org(rf, core_developer):
    project = ProjectFactory()
    ProjectFactory.create_batch(2)

    request = rf.get(f"/?org={project.org.slug}")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert len(response.context_data["project_list"]) == 1


def test_projectlist_find_by_username(rf, core_developer):
    ProjectFactory(name="ben")
    ProjectFactory(name="benjamin")
    ProjectFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["project_list"]) == 2


def test_projectlist_success(rf, core_developer):
    ProjectFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["project_list"])


def test_projectlist_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectList.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
        )


def test_projectmembershipedit_success(rf, core_developer):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    membership = ProjectMembershipFactory(project=project, user=UserFactory())

    request = rf.post("/", {"roles": [dotted_path(ProjectDeveloper)]})
    request.user = core_developer

    response = ProjectMembershipEdit.as_view()(
        request, slug=project.slug, pk=membership.pk
    )

    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    membership.refresh_from_db()
    assert membership.roles == [ProjectDeveloper]


def test_projectmembershipedit_unknown_membership(rf, core_developer):
    project = ProjectFactory()

    ProjectMembershipFactory(project=project, user=UserFactory())

    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ProjectMembershipEdit.as_view()(request, slug=project.slug, pk="0")


def test_projectmembershipedit_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectMembershipEdit.as_view()(request)


def test_projectmembershipremove_success(rf, core_developer):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user)

    request = rf.post("/", {"username": user.username})
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectMembershipRemove.as_view()(request, slug=project.slug)

    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    project.refresh_from_db()
    assert user not in project.members.all()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == f"Removed {user.username} from {project.name}"


def test_projectmembershipremove_unauthorized(rf):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectMembershipRemove.as_view()(request)


def test_projectmembershipremove_unknown_project(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ProjectMembershipRemove.as_view()(request, slug="test")


def test_projectmembershipremove_unknown_member(rf, core_developer):
    project = ProjectFactory()

    assert project.memberships.count() == 0

    request = rf.post("/", {"username": "test"})
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages
    response = ProjectMembershipRemove.as_view()(request, slug=project.slug)
    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    project.refresh_from_db()
    assert project.memberships.count() == 0
