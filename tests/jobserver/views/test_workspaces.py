import zipfile

import pytest
import responses
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import ProjectCollaborator, ProjectDeveloper
from jobserver.models import Backend, JobRequest, Workspace
from jobserver.views.workspaces import (
    WorkspaceArchiveToggle,
    WorkspaceBackendFiles,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceFileList,
    WorkspaceLatestOutputsDetail,
    WorkspaceLatestOutputsDownload,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceOutputList,
)

from ...factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...utils import minutes_ago


MEANINGLESS_URL = "/"


@pytest.mark.django_db
@responses.activate
def test_workspacearchivetoggle_success(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, is_archived=False)

    request = rf.post(MEANINGLESS_URL, {"is_archived": "True"})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceArchiveToggle.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == "/"

    workspace.refresh_from_db()
    assert workspace.is_archived


@pytest.mark.django_db
@responses.activate
def test_workspacearchivetoggle_unauthorized(rf, user):
    workspace = WorkspaceFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceArchiveToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
def test_workspacebackendfiles_success(rf):
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceBackendFiles.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        backend_slug=backend.name,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_workspacebackendfiles_unknown_backend(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceBackendFiles.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            backend_slug="unknown",
        )


@pytest.mark.django_db
def test_workspacebackendfiles_unknown_workspace(rf):
    backend = BackendFactory()
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceBackendFiles.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="unknown",
            backend_slug=backend.name,
        )


@pytest.mark.django_db
def test_workspacebackendfiles_with_permission(rf):
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceBackendFiles.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        backend_slug=backend.name,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_workspacebackendfiles_without_backend_access(rf):
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceBackendFiles.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            backend_slug=backend.name,
        )


@pytest.mark.django_db
def test_workspacebackendfiles_without_permission(rf):
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceBackendFiles.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            backend_slug=backend.name,
        )


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_get_success(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    mocker.patch(
        "jobserver.views.workspaces.get_repos_with_branches",
        autospec=True,
        return_value=[],
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_get_without_permission(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    mocker.patch(
        "jobserver.views.workspaces.get_repos_with_branches",
        autospec=True,
        return_value=[],
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    with pytest.raises(Http404):
        WorkspaceCreate.as_view()(request, org_slug=org.slug, project_slug=project.slug)


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_post_success(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    mocker.patch(
        "jobserver.views.workspaces.get_repos_with_branches",
        autospec=True,
        return_value=[{"name": "Test", "url": "test", "branches": ["test"]}],
    )

    data = {
        "name": "Test",
        "repo": "test",
        "branch": "test",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceCreate.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302

    workspace = Workspace.objects.first()
    assert response.url == workspace.get_absolute_url()
    assert workspace.created_by == user


@pytest.mark.django_db
@responses.activate
def test_workspacecreate_unauthorized(rf, user):
    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceCreate.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
def test_workspacedetail_logged_out(rf):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_workspacedetail_project_yaml_errors(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project",
        autospec=True,
        side_effect=Exception("test error"),
    )
    mocker.patch(
        "jobserver.views.workspaces.get_repo_is_private",
        autospec=True,
        return_value=True,
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == []
    assert response.context_data["actions_error"] == "test error"


@pytest.mark.django_db
def test_workspacedetail_get_success(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    # Give the User the permission to view unpublished Snapshots and current
    # Workspace files
    user.roles = [ProjectCollaborator]
    user.save()

    # set up some files for the workspace
    upload = ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"})
    ReleaseFactory(upload, workspace=workspace)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_repo_is_private",
        autospec=True,
        return_value=True,
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace

    # this is true because the user has the right permission to see outputs
    assert response.context_data["user_can_view_outputs"]


@pytest.mark.django_db
def test_workspacedetail_get_with_access_to_files(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    # Give the User the permission to view unpublished Snapshots and current
    # Workspace files
    user.roles = [ProjectCollaborator]
    user.save()

    # set up some files for the workspace
    upload = ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"})
    ReleaseFactory(upload, workspace=workspace)

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_repo_is_private",
        autospec=True,
        return_value=True,
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace

    # this is false because while the user can view outputs, but they have no
    # Backends with a level 4 URL set up.
    assert not response.context_data["user_can_view_files"]


@pytest.mark.django_db
def test_workspacedetail_get_with_unprivileged_user(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_repo_is_private",
        autospec=True,
        return_value=True,
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["actions"] == [
        {"name": "twiddle", "needs": [], "status": "-"},
        {"name": "run_all", "needs": ["twiddle"], "status": "-"},
    ]
    assert response.context_data["workspace"] == workspace

    # this is false because:
    # the user is either logged out
    #   OR doesn't have the right permission to see outputs
    #   AND there are no published Snapshots to show the user.
    assert not response.context_data["user_can_view_outputs"]


@pytest.mark.django_db
def test_workspacedetail_post_archived_workspace(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, is_archived=True)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_actions", autospec=True, return_value=[]
    )

    request = rf.post(MEANINGLESS_URL)
    request.session = "session"
    request._messages = FallbackStorage(request)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()


@pytest.mark.django_db
def test_workspacedetail_post_success(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp")

    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_workspacedetail_post_with_invalid_backend(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp,emis")

    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )
    mocker.patch(
        "jobserver.views.workspaces.get_repo_is_private",
        autospec=True,
        return_value=True,
    )

    data = {
        "backend": "emis",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["form"].errors["backend"] == [
        "Select a valid choice. emis is not one of the available choices."
    ]


@pytest.mark.django_db
def test_workspacedetail_post_with_notifications_default(rf, mocker, monkeypatch, user):
    monkeypatch.setenv("BACKENDS", "tpp")

    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "True",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert job_request.will_notify


@pytest.mark.django_db
def test_workspacedetail_post_with_notifications_override(
    rf, mocker, monkeypatch, user
):
    monkeypatch.setenv("BACKENDS", "tpp")

    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, should_notify=True)

    BackendMembershipFactory(backend=Backend.objects.get(name="tpp"), user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    dummy_yaml = """
    actions:
      twiddle:
    """
    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )
    mocker.patch(
        "jobserver.views.workspaces.get_project", autospec=True, return_value=dummy_yaml
    )
    mocker.patch(
        "jobserver.views.workspaces.get_branch_sha",
        autospec=True,
        return_value="abc123",
    )

    data = {
        "backend": "tpp",
        "requested_actions": ["twiddle"],
        "callback_url": "test",
        "will_notify": "False",
    }
    request = rf.post(MEANINGLESS_URL, data)
    request.user = user

    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_logs_url()

    job_request = JobRequest.objects.first()
    assert job_request.created_by == user
    assert job_request.workspace == workspace
    assert job_request.backend.name == "tpp"
    assert job_request.requested_actions == ["twiddle"]
    assert job_request.sha == "abc123"
    assert not job_request.will_notify
    assert not job_request.jobs.exists()


@pytest.mark.django_db
def test_workspacedetail_unknown_workspace(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = user
    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug="test",
    )

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_workspacedetail_get_with_unauthenticated_user(rf, user):
    """
    Check WorkspaceDetail does not render the controls for Archiving,
    Notifications, and selecting Actions for unauthenticated Users.
    """
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, is_archived=False)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = WorkspaceDetail.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert "Archive" not in response.rendered_content
    assert "Turn Notifications" not in response.rendered_content
    assert "twiddle" not in response.rendered_content


@pytest.mark.django_db
def test_workspacefilelist_success(rf):
    backend1 = BackendFactory()
    BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend1, user=user)
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceFileList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert list(response.context_data["backends"]) == [backend1]


@pytest.mark.django_db
def test_workspacefilelist_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceFileList.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


@pytest.mark.django_db
def test_workspacefilelist_without_backends(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceFileList.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacefilelist_without_permission(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(user=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceFileList.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacelatestoutputsdetail_success(rf):
    user = UserFactory(roles=[ProjectCollaborator])
    workspace = WorkspaceFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceLatestOutputsDetail.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["prepare_url"]


@pytest.mark.django_db
def test_workspacelatestoutputsdetail_without_file_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDetail.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacelatestoutputsdetail_without_publish_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceLatestOutputsDetail.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert not response.context_data["prepare_url"]


@pytest.mark.django_db
def test_workspacelatestoutputsdetail_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDetail.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


@pytest.mark.django_db
def test_workspacelatestoutputsdownload_no_files(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacelatestoutputsdownload_success(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1", "test2"]), workspace=workspace)
    ReleaseFactory(ReleaseUploadsFactory(["test3"]), workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceLatestOutputsDownload.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    # check the returned file has the 3 files in it
    with zipfile.ZipFile(response.file_to_stream, "r") as zip_obj:
        assert zip_obj.testzip() is None

        assert set(zip_obj.namelist()) == {"test1", "test2", "test3"}


@pytest.mark.django_db
def test_workspacelatestoutputsdownload_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDownload.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


@pytest.mark.django_db
def test_workspacelatestoutputsdownload_without_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacelog_search_by_action(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    job_request1 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, action="leap")

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get("/?q=run")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


@pytest.mark.django_db
def test_workspacelog_search_by_id(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request2, id=99)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get("/?q=99")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


@pytest.mark.django_db
def test_workspacelog_success(rf, mocker, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1


@pytest.mark.django_db
def test_workspacelog_unknown_workspace(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()
    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug="test",
    )

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_workspacelog_with_authenticated_user(rf, mocker, user):
    """
    Check WorkspaceLog renders the Add Job button for authenticated Users
    """
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    mocker.patch(
        "jobserver.views.workspaces.can_run_jobs", autospec=True, return_value=True
    )

    request = rf.get(MEANINGLESS_URL)
    request.user = UserFactory()

    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert "Add Job" in response.rendered_content


@pytest.mark.django_db
def test_workspacelog_with_unauthenticated_user(rf, user):
    """
    Check WorkspaceLog renders the Add Job button for authenticated Users
    """
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    # Build a RequestFactory instance
    request = rf.get(MEANINGLESS_URL)
    request.user = AnonymousUser()
    response = WorkspaceLog.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert "Add Job" not in response.rendered_content


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_success(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project, should_notify=True)

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    response = WorkspaceNotificationsToggle.as_view()(
        request,
        org_slug=org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    assert not workspace.should_notify


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unauthorized(rf, user):
    workspace = WorkspaceFactory()

    request = rf.post(MEANINGLESS_URL, {"should_notify": ""})
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=404)

    response = WorkspaceNotificationsToggle.as_view()(request, name=workspace.name)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


@pytest.mark.django_db
@responses.activate
def test_workspacenotificationstoggle_unknown_workspace(rf, user):
    org = user.orgs.first()
    project = ProjectFactory(org=org)

    request = rf.post(MEANINGLESS_URL)
    request.user = user

    gh_org = user.orgs.first().github_orgs[0]
    membership_url = f"https://api.github.com/orgs/{gh_org}/members/{user.username}"
    responses.add(responses.GET, membership_url, status=204)

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(
            request, org_slug=org.slug, project_slug=project.slug, workspace_slug="test"
        )


@pytest.mark.django_db
def test_workspaceoutputlist_success(rf, freezer):
    workspace = WorkspaceFactory()

    now = timezone.now()

    ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"}),
        workspace=workspace,
    )
    snapshot1 = SnapshotFactory(workspace=workspace, published_at=minutes_ago(now, 3))
    snapshot1.files.set(workspace.files.all())

    ReleaseFactory(
        ReleaseUploadsFactory(
            {
                "file2.txt": b"text2",
                "file3.txt": b"text",
            }
        ),
        workspace=workspace,
    )
    snapshot2 = SnapshotFactory(workspace=workspace)
    snapshot2.files.set(workspace.files.all())

    ReleaseFactory(
        ReleaseUploadsFactory(
            {
                "file2.txt": b"text2",
                "file3.txt": b"text",
            }
        ),
        workspace=workspace,
    )

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceOutputList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["snapshots"]) == 2


@pytest.mark.django_db
def test_workspaceoutputlist_without_permission(rf, freezer):
    workspace = WorkspaceFactory()

    now = timezone.now()

    ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"}),
        workspace=workspace,
    )
    snapshot1 = SnapshotFactory(workspace=workspace, published_at=minutes_ago(now, 3))
    snapshot1.files.set(workspace.files.all())

    ReleaseFactory(
        ReleaseUploadsFactory(
            {
                "file2.txt": b"text2",
                "file3.txt": b"text",
            }
        ),
        workspace=workspace,
    )
    snapshot2 = SnapshotFactory(workspace=workspace, published_at=None)
    snapshot2.files.set(workspace.files.all())

    ReleaseFactory(
        ReleaseUploadsFactory(
            {
                "file2.txt": b"text2",
                "file3.txt": b"text",
            }
        ),
        workspace=workspace,
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceOutputList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["snapshots"]) == 1

    # Check we're not showing the latest files section for an unprivileged user
    assert "Current" not in response.rendered_content


@pytest.mark.django_db
def test_workspaceoutputlist_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceOutputList.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )
