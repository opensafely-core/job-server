import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404

from jobserver.authorization import ProjectCoordinator
from jobserver.models import Project, ProjectInvitation, ProjectMembership
from jobserver.views.projects import (
    ProjectCreate,
    ProjectDetail,
    ProjectDisconnectWorkspace,
    ProjectRemoveMember,
    ProjectSettings,
)

from ...factories import (
    OrgFactory,
    ProjectFactory,
    ProjectInvitationFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_projectcreate_get_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectcreate_get_unknown_org(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectcreate_post_invalid_data(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "",
        "project_lead": "",
        "email": "",
        "researcher-TOTAL_FORMS": "0",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert Project.objects.count() == 0


@pytest.mark.django_db
def test_projectcreate_post_success(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "A Brand New Project",
        "project_lead": "My Name",
        "email": "name@example.com",
        "researcher-TOTAL_FORMS": "1",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
        "researcher-0-name": "Test",
        "researcher-0-passed_researcher_training_at": "2021-01-01",
        "researcher-0-is_ons_accredited_researcher": "on",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 302

    projects = Project.objects.all()
    assert len(projects) == 1

    project = projects.first()
    assert project.name == "A Brand New Project"
    assert project.project_lead == "My Name"
    assert project.email == "name@example.com"
    assert project.org == org
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectcreate_post_unknown_org(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectdetail_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectDetail.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectdetail_unknown_org(rf, superuser):
    project = ProjectFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug="test", project_slug=project.slug)


@pytest.mark.django_db
def test_projectdetail_unknown_project(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug=org.slug, project_slug="test")


@pytest.mark.django_db
def test_projectdisconnect_missing_workspace_id(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectDisconnectWorkspace.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectdisconnect_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    request = rf.post(MEANINGLESS_URL, {"id": workspace.pk})
    request.user = superuser
    response = ProjectDisconnectWorkspace.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectdisconnect_unknown_project(rf, superuser):
    org = OrgFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDisconnectWorkspace.as_view()(
            request, org_slug=org.slug, project_slug=""
        )


@pytest.mark.django_db
def test_projectremovemember_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    member = UserFactory()

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )
    membership = ProjectMembershipFactory(project=project, user=member)

    request = rf.post("/", {"username": member.username})
    request.user = superuser

    response = ProjectRemoveMember.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


@pytest.mark.django_db
def test_projectremovemember_unknown_project_membership(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )

    request = rf.post("/", {"username": "test"})
    request.user = superuser

    with pytest.raises(Http404):
        ProjectRemoveMember.as_view()(
            request, org_slug=org.slug, project_slug=project.slug
        )


@pytest.mark.django_db
def test_projectremovemember_without_permission(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    member = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=member)

    request = rf.post("/", {"username": member.username})
    request.user = superuser

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ProjectRemoveMember.as_view()(
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


@pytest.mark.django_db
def test_projectsettings_get_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    response = ProjectSettings.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["members"]) == 1
    assert response.context_data["project"] == project


@pytest.mark.django_db
def test_projectsettings_post_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invitee = UserFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )

    ProjectInvitationFactory(project=project, user=invitee)
    assert ProjectInvitation.objects.filter(project=project).count() == 1

    request = rf.post(MEANINGLESS_URL, {"users": [str(user.pk)]})
    request.user = superuser

    response = ProjectSettings.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_settings_url()

    assert ProjectInvitation.objects.filter(project=project).count() == 2
    assert ProjectInvitation.objects.filter(project=project, user=user).exists()


@pytest.mark.django_db
def test_projectsettings_post_with_email_failure(rf, superuser, mocker):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    invitee = UserFactory()

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )

    request = rf.post(MEANINGLESS_URL, {"users": [str(invitee.pk)]})
    request.user = superuser

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    # mock send_project_invite_email to throw an exception
    mocker.patch(
        "jobserver.views.projects.send_project_invite_email",
        autospec=True,
        side_effect=Exception,
    )
    response = ProjectSettings.as_view()(
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


@pytest.mark.django_db
def test_projectsettings_post_with_incorrect_form(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    ProjectMembershipFactory(
        project=project, user=superuser, roles=[ProjectCoordinator]
    )

    ProjectInvitationFactory(project=project)
    assert ProjectInvitation.objects.filter(project=project).count() == 1

    request = rf.post(MEANINGLESS_URL, {"users": ["not_a_pk"]})
    request.user = superuser

    response = ProjectSettings.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    # check the number of invitations hasn't changed
    assert ProjectInvitation.objects.filter(project=project).count() == 1

    assert "“not_a_pk” is not a valid value." in response.rendered_content


@pytest.mark.django_db
def test_projectsettings_unknown_project(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    with pytest.raises(Http404):
        ProjectSettings.as_view()(request, org_slug="", project_slug="")


@pytest.mark.django_db
def test_projectsettings_without_permission(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    with pytest.raises(Http404):
        ProjectSettings.as_view()(request, org_slug=org.slug, project_slug=project.slug)
