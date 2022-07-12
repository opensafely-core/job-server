import pytest
import requests
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import (
    CoreDeveloper,
    ProjectCollaborator,
    ProjectCoordinator,
    ProjectDeveloper,
)
from jobserver.models import ProjectInvitation, ProjectMembership, Snapshot
from jobserver.utils import dotted_path, set_from_qs
from jobserver.views.projects import (
    ProjectAcceptInvite,
    ProjectCancelInvite,
    ProjectDetail,
    ProjectInvitationCreate,
    ProjectMembershipEdit,
    ProjectMembershipRemove,
    ProjectSettings,
)

from ....factories import (
    OrgFactory,
    ProjectFactory,
    ProjectInvitationFactory,
    ProjectMembershipFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI
from ....utils import minutes_ago


def test_projectacceptinvite_already_accepted(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=user)
    invite = ProjectInvitationFactory(
        project=project,
        user=user,
        membership=membership,
        roles=[ProjectCollaborator],
    )

    request = rf.get("/")
    request.user = user

    response = ProjectAcceptInvite.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        signed_pk=invite.signed_pk,
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()

    assert ProjectMembership.objects.filter(project=project, user=user).count() == 1


def test_projectacceptinvite_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()

    invite = ProjectInvitationFactory(
        project=project, user=user, roles=[ProjectCollaborator]
    )
    assert invite.membership is None

    request = rf.get("/")
    request.user = user

    response = ProjectAcceptInvite.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        signed_pk=invite.signed_pk,
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()

    invite.refresh_from_db()
    assert invite.membership is not None
    assert invite.membership.project == project
    assert invite.membership.roles == invite.roles
    assert invite.membership.roles == [ProjectCollaborator]


def test_projectacceptinvite_unknown_invite(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectAcceptInvite.as_view()(
            request,
            org_slug=org.slug,
            project_slug=project.slug,
            signed_pk="test",
        )


def test_projectacceptinvite_with_different_user(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invitee = UserFactory()
    invite = ProjectInvitationFactory(project=project, user=invitee)

    request = rf.get("/")
    request.user = UserFactory()

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectAcceptInvite.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        signed_pk=invite.signed_pk,
    )

    assert response.status_code == 302
    assert response.url == "/"

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Only the User who was invited may accept an invite."


def test_projectcancelinvite_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    invite = ProjectInvitationFactory(project=project, user=user)

    request = rf.post("/", {"invite_pk": invite.pk})
    request.user = user

    response = ProjectCancelInvite.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    assert not ProjectInvitation.objects.filter(pk=invite.pk).exists()


def test_projectcancelinvite_unknown_invitation(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    request = rf.post("/", {"invite_pk": 0})
    request.user = user

    with pytest.raises(Http404):
        ProjectCancelInvite.as_view()(
            request, org_slug=org.slug, project_slug=project.slug
        )


def test_projectcancelinvite_without_manage_members_permission(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invite = ProjectInvitationFactory(project=project, user=UserFactory())

    request = rf.post("/", {"invite_pk": invite.pk})
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectCancelInvite.as_view()(
            request, org_slug=org.slug, project_slug=project.slug
        )


def test_projectdetail_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    WorkspaceFactory.create_batch(
        3,
        project=project,
        repo="https://github.com/opensafely/some-research",
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["repos"]) == 1
    assert response.context_data["repos"] == [
        {
            "name": "some-research",
            "url": "https://github.com/opensafely/some-research",
            "is_private": True,
        }
    ]

    # check the staff-only edit link doesn't show for normal users
    assert "Edit" not in response.context_data


def test_projectdetail_with_multiple_releases(rf, freezer):
    project = ProjectFactory()

    now = timezone.now()

    workspace1 = WorkspaceFactory(project=project)
    snapshot1 = SnapshotFactory(workspace=workspace1, published_at=minutes_ago(now, 2))
    snapshot2 = SnapshotFactory(workspace=workspace1, published_at=minutes_ago(now, 3))

    workspace2 = WorkspaceFactory(project=project)
    snapshot3 = SnapshotFactory(workspace=workspace2, published_at=minutes_ago(now, 1))

    # unpublished
    workspace3 = WorkspaceFactory(project=project)
    snapshot4 = SnapshotFactory(workspace=workspace3, published_at=None)

    workspace4 = WorkspaceFactory(project=project)
    snapshot5 = SnapshotFactory(workspace=workspace4, published_at=minutes_ago(now, 4))

    request = rf.get("/")
    # FIXME: remove this role when releases is deployed to all users
    request.user = UserFactory(roles=[CoreDeveloper])

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert "Outputs" in response.rendered_content

    # check the ordering of responses, should be latest first
    assert len(response.context_data["outputs"]) == 3
    output_pks = list(response.context_data["outputs"].values_list("pk", flat=True))
    expected_pks = [snapshot3.pk, snapshot1.pk, snapshot5.pk]
    assert output_pks == expected_pks

    # check unpublished or published-but-older snapshots are not in the
    # snapshots picked to display for outputs
    snapshots = set_from_qs(Snapshot.objects.all())
    assert snapshot2 not in snapshots
    assert snapshot4 not in snapshots


def test_projectdetail_with_no_github(rf):
    project = ProjectFactory()
    WorkspaceFactory(project=project)

    request = rf.get("/")
    request.user = UserFactory()

    class BrokenGitHubAPI:
        def get_repo_is_private(self, *args):
            raise requests.HTTPError

    response = ProjectDetail.as_view(get_github_api=BrokenGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    # check there is no public/private badge when GitHub returns an
    # unsuccessful response
    assert response.context_data["repos"][0]["is_private"] is None
    assert "Private" not in response.rendered_content
    assert "Public" not in response.rendered_content


def test_projectdetail_with_no_releases(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["outputs"]) == 0
    assert "Outputs" not in response.rendered_content


def test_projectdetail_unknown_org(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug="test", project_slug=project.slug)


def test_projectdetail_unknown_project(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug=org.slug, project_slug="test")


def test_projectinvitationcreate_get_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )

    request = rf.get("/")
    request.user = coordinator

    response = ProjectInvitationCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


def test_projectinvitationcreate_post_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()
    invitee = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )

    assert ProjectInvitation.objects.filter(project=project).count() == 0

    request = rf.post(
        "/",
        {
            "roles": ["jobserver.authorization.roles.ProjectDeveloper"],
            "users": [str(invitee.pk)],
        },
    )
    request.user = coordinator

    response = ProjectInvitationCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    assert ProjectInvitation.objects.filter(project=project).count() == 1

    invitation = ProjectInvitation.objects.get(project=project, user=invitee)
    assert invitation.roles == [ProjectDeveloper]


def test_projectinvitationcreate_post_with_email_failure(rf, mocker):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()
    invitee = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )

    # mock send_project_invite_email to throw an exception
    mocker.patch(
        "jobserver.views.projects.send_project_invite_email",
        autospec=True,
        side_effect=Exception,
    )

    request = rf.post(
        "/",
        {
            "roles": ["jobserver.authorization.roles.ProjectDeveloper"],
            "users": [str(invitee.pk)],
        },
    )
    request.user = coordinator

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectInvitationCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    # check there are no invitations
    assert not ProjectInvitation.objects.exists()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    expected = f"<p>Failed to invite 1 User(s):</p><ul><li>{invitee.username}</li></ul><p>Please try again.</p>"
    assert str(messages[0]) == expected


def test_projectinvitationcreate_post_with_incorrect_form(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )

    assert ProjectInvitation.objects.filter(project=project).count() == 0

    request = rf.post("/", {"roles": ["foo"], "users": ["not_a_pk"]})
    request.user = coordinator

    response = ProjectInvitationCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    # check the number of invitations hasn't changed
    assert ProjectInvitation.objects.filter(project=project).count() == 0

    assert "not_a_pk is not one of the available choices." in response.rendered_content


def test_projectinvitationcreate_without_permission(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        ProjectInvitationCreate.as_view()(
            request, org_slug=org.slug, project_slug=project.slug
        )


def test_projectmembershipedit_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    membership = ProjectMembershipFactory(project=project, user=UserFactory())

    request = rf.post("/", {"roles": [dotted_path(ProjectDeveloper)]})
    request.user = user

    response = ProjectMembershipEdit.as_view()(
        request, org_slug=org.slug, project_slug=project.slug, pk=membership.pk
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    membership.refresh_from_db()
    assert membership.roles == [ProjectDeveloper]


def test_projectmembershipedit_unknown_membership(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        ProjectMembershipEdit.as_view()(
            request, org_slug=org.slug, project_slug=project.slug, pk="0"
        )


def test_projectmembershipedit_without_permission(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectMembershipEdit.as_view()(
        request, org_slug=org.slug, project_slug=project.slug, pk="0"
    )
    assert response.status_code == 302
    assert response.url == project.get_settings_url()


def test_projectmembershipremove_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()
    member = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )
    membership = ProjectMembershipFactory(project=project, user=member)

    request = rf.post("/", {"member_pk": membership.pk})
    request.user = coordinator

    response = ProjectMembershipRemove.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


def test_projectmembershipremove_unknown_project_membership(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.post("/", {"member_pk": 0})
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectMembershipRemove.as_view()(
            request, org_slug=org.slug, project_slug=project.slug
        )


def test_projectmembershipremove_without_permission(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    member = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=member)

    request = rf.post("/", {"member_pk": membership.pk})
    request.user = UserFactory()

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectMembershipRemove.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    # confirm the membership hasn't been deleted
    assert ProjectMembership.objects.filter(pk=membership.pk).exists()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "You do not have permission to remove Project members."


def test_projectsettings_success(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    coordinator = UserFactory()

    ProjectMembershipFactory(
        project=project, user=coordinator, roles=[ProjectCoordinator]
    )

    request = rf.get("/")
    request.user = coordinator

    response = ProjectSettings.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["memberships"]) == 1
    assert response.context_data["project"] == project


def test_projectsettings_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        ProjectSettings.as_view()(request, org_slug="", project_slug="")


def test_projectsettings_without_permission(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        ProjectSettings.as_view()(request, org_slug=org.slug, project_slug=project.slug)
