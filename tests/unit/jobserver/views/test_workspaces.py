import zipfile
from datetime import timedelta

import pytest
import requests
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import (
    CoreDeveloper,
    OpensafelyInteractive,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models import Workspace
from jobserver.views.workspaces import (
    WorkspaceArchiveToggle,
    WorkspaceBackendFiles,
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceEdit,
    WorkspaceFileList,
    WorkspaceLatestOutputsDetail,
    WorkspaceLatestOutputsDownload,
    WorkspaceLog,
    WorkspaceNotificationsToggle,
    WorkspaceOutputList,
)

from ....factories import (
    BackendFactory,
    BackendMembershipFactory,
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    RepoFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI
from ....utils import minutes_ago


def test_workspacearchivetoggle_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory(is_archived=False)

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/", {"is_archived": "True"})
    request.user = user

    response = WorkspaceArchiveToggle.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.project.get_absolute_url()

    workspace.refresh_from_db()
    assert workspace.is_archived


def test_workspacearchivetoggle_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceArchiveToggle.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


def test_workspacearchivetoggle_without_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceArchiveToggle.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


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
        backend_slug=backend.slug,
    )

    assert response.status_code == 200


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
            backend_slug=backend.slug,
        )


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
        backend_slug=backend.slug,
    )

    assert response.status_code == 200


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
            backend_slug=backend.slug,
        )


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
            backend_slug=backend.slug,
        )


def test_workspacecreate_get_success(rf, user):
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = user

    response = WorkspaceCreate.as_view(get_github_api=FakeGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


def test_workspacecreate_get_without_permission(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceCreate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
        )


def test_workspacecreate_post_success(rf, user):
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    data = {
        "name": "Test",
        "repo": "test",
        "branch": "main",
        "purpose": "test",
    }
    request = rf.post("/", data)
    request.user = user

    response = WorkspaceCreate.as_view(get_github_api=FakeGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 302, response.context_data["form"].errors

    workspace = Workspace.objects.first()
    assert response.url == workspace.get_absolute_url()
    assert workspace.created_by == user


def test_workspacecreate_without_github(rf, user):
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = user

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    class BrokenGitHubAPI:
        def get_repos_with_branches(self, *args):
            raise requests.HTTPError

    response = WorkspaceCreate.as_view(get_github_api=BrokenGitHubAPI)(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    # check we skipped creating the form
    assert "form" not in response.context_data

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1

    expected = (
        "An error occurred while retrieving the list of repositories from GitHub, "
        "please reload the page to try again."
    )
    assert str(messages[0]) == expected


def test_workspacecreate_without_github_orgs(rf):
    user = UserFactory()

    org = OrgFactory(github_orgs=[])
    OrgMembershipFactory(org=org, user=user)

    project = ProjectFactory(org=org)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = user

    response = WorkspaceCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200
    assert response.template_name == "workspace_create_error.html"


def test_workspacecreate_without_org(rf):
    user = UserFactory()

    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = user

    response = WorkspaceCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200
    assert response.template_name == "workspace_create_error.html"


def test_workspacecreate_without_permission(rf, user):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceCreate.as_view()(
            request, org_slug=project.org.slug, project_slug=project.slug
        )


def test_workspacedetail_authorized_archive_workspaces(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_archive_workspace"]


def test_workspacedetail_authorized_public_repo_hide_change_visibility_banner(rf):
    project = ProjectFactory()

    # a workspace with a "private" repo which ran its first job > 11 months ago
    private = WorkspaceFactory(
        project=project, repo=RepoFactory(url="http://example.com/repo/private")
    )
    job_request = JobRequestFactory(workspace=private)
    JobFactory(job_request=job_request, started_at=timezone.now() - timedelta(weeks=52))

    # the workspace we're viewing, which is using a "public" repo
    workspace = WorkspaceFactory(
        project=project, repo=RepoFactory(url="http://example.com/repo/public")
    )

    user = UserFactory()
    BackendMembershipFactory(user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    # this is what defines "private"
    class AnotherFakeGitHubAPI:
        def get_repo_is_private(self, owner, name):
            return name.startswith("private")

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=AnotherFakeGitHubAPI)(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert not response.context_data["show_publish_repo_warning"]


def test_workspacedetail_authorized_private_repo_show_change_visibility_banner(rf):
    project = ProjectFactory()

    # a workspace with a "private" repo which ran its first job > 11 months ago
    private = WorkspaceFactory(
        project=project, repo=RepoFactory(url="http://example.com/repo/private1")
    )
    job_request = JobRequestFactory(workspace=private)
    JobFactory(job_request=job_request, started_at=timezone.now() - timedelta(weeks=52))

    # the workspace we're viewing, which is also using a "private" repo
    workspace = WorkspaceFactory(
        project=project, repo=RepoFactory(url="http://example.com/repo/private2")
    )

    user = UserFactory()
    BackendMembershipFactory(user=user)
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    # this is what defines "private"
    class AnotherFakeGitHubAPI:
        def get_repo_is_private(self, owner, name):
            return name.startswith("private")

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=AnotherFakeGitHubAPI)(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["show_publish_repo_warning"]


def test_workspacedetail_authorized_view_files(rf):
    backend = BackendFactory(level_4_url="http://test/")
    user = UserFactory(roles=[ProjectCollaborator])
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_view_files"]


def test_workspacedetail_authorized_view_releases(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_view_releases"]


def test_workspacedetail_authorized_run_jobs(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_run_jobs"]
    assert response.context_data["run_jobs_url"] == workspace.get_jobs_url()


def test_workspacedetail_authorized_run_jobs_with_opensafely_interactive_role(rf):
    workspace = WorkspaceFactory()
    user = UserFactory(roles=[OpensafelyInteractive])

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["run_jobs_url"] == workspace.get_pick_ref_url()


def test_workspacedetail_authorized_view_snaphots(rf):
    workspace = WorkspaceFactory()
    SnapshotFactory(
        workspace=workspace, published_by=UserFactory(), published_at=timezone.now()
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["user_can_view_outputs"]


def test_workspacedetail_authorized_honeycomb(rf):
    workspace = WorkspaceFactory()
    SnapshotFactory(
        workspace=workspace, published_by=UserFactory(), published_at=timezone.now()
    )

    request = rf.get("/")
    request.user = UserFactory(roles=[CoreDeveloper])

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert "Honeycomb" in response.rendered_content
    assert (
        f"workspace_name%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22{workspace.name}"
        in response.rendered_content
    )


def test_workspacedetail_logged_out(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    # this is false because while the user can view outputs, but they have no
    # Backends with a level 4 URL set up.
    assert not response.context_data["user_can_view_files"]

    assert not response.context_data["user_can_run_jobs"]
    assert not response.context_data["user_can_view_releases"]

    # this is false because:
    # the user is either logged out
    #   OR doesn't have the right permission to see outputs
    #   AND there are no published Snapshots to show the user.
    assert not response.context_data["user_can_view_outputs"]


def test_workspacedetail_unauthorized(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceDetail.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    # this is false because while the user can view outputs, but they have no
    # Backends with a level 4 URL set up.
    assert not response.context_data["user_can_view_files"]

    assert not response.context_data["user_can_run_jobs"]
    assert not response.context_data["user_can_view_releases"]

    # this is false because:
    # the user is either logged out
    #   OR doesn't have the right permission to see outputs
    #   AND there are no published Snapshots to show the user.
    assert not response.context_data["user_can_view_outputs"]


def test_workspacedetail_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceDetail.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


def test_workspacedetail_with_no_github(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    class BrokenGitHubAPI:
        def get_repo_is_private(self, *args):
            raise requests.HTTPError

    response = WorkspaceDetail.as_view(get_github_api=BrokenGitHubAPI)(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["repo_is_private"] is None


def test_workspaceedit_get_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.get("/")
    request.user = user

    response = WorkspaceEdit.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspaceedit_get_without_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        WorkspaceEdit.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_workspaceedit_post_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/", {"purpose": "test"})
    request.user = user

    response = WorkspaceEdit.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()
    assert workspace.purpose == "test"


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


def test_workspacelatestoutputsdownload_success(rf, build_release_with_files):
    workspace = WorkspaceFactory()
    build_release_with_files(["test1", "test2"], workspace=workspace)
    build_release_with_files(["test3"], workspace=workspace)

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


def test_workspacelatestoutputsdownload_without_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFileFactory(workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        WorkspaceLatestOutputsDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_workspacelog_filter_by_one_backend(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    backend = BackendFactory()
    job_request1 = JobRequestFactory(workspace=workspace, backend=backend)

    JobRequestFactory(workspace=workspace, backend=BackendFactory())

    request = rf.get(f"/?backend={backend.slug}")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


def test_workspacelog_filter_by_several_backends(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    JobRequestFactory(workspace=workspace, backend=BackendFactory())

    backend1 = BackendFactory()
    job_request1 = JobRequestFactory(workspace=workspace, backend=backend1)

    backend2 = BackendFactory()
    job_request2 = JobRequestFactory(workspace=workspace, backend=backend2)

    backend3 = BackendFactory()
    job_request3 = JobRequestFactory(workspace=workspace, backend=backend3)

    request = rf.get(
        f"/?backend={backend1.slug}&backend={backend2.slug}&backend={backend3.slug}"
    )
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 3
    assert set(response.context_data["object_list"]) == {
        job_request1,
        job_request2,
        job_request3,
    }


def test_workspacelog_search_by_action(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    job_request1 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request1, action="run")

    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, action="leap")

    request = rf.get("/?q=run")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request1


def test_workspacelog_search_by_id(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    JobFactory(job_request=JobRequestFactory())

    job_request2 = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request2, id=99)

    request = rf.get("/?q=99")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert len(response.context_data["object_list"]) == 1
    assert response.context_data["object_list"][0] == job_request2


def test_workspacelog_success(rf):
    workspace = WorkspaceFactory()
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    job_request = JobRequestFactory(created_by=user, workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1


def test_workspacelog_unknown_workspace(rf):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = user

    response = WorkspaceLog.as_view()(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        workspace_slug="test",
    )

    assert response.status_code == 302
    assert response.url == "/"


def test_workspacelog_with_authenticated_user(rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacelog_with_unauthenticated_user(rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = WorkspaceLog.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenotificationstoggle_success(rf):
    workspace = WorkspaceFactory(should_notify=True)
    user = UserFactory()

    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = rf.post("/", {"should_notify": ""})
    request.user = user

    response = WorkspaceNotificationsToggle.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    assert not workspace.should_notify


def test_workspacenotificationstoggle_without_permission(rf, user):
    workspace = WorkspaceFactory()
    user = UserFactory()

    request = rf.post("/", {"should_notify": ""})
    request.user = user

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_workspacenotificationstoggle_unknown_workspace(rf):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.post("/")
    request.user = user

    with pytest.raises(Http404):
        WorkspaceNotificationsToggle.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="test",
        )


def test_workspaceoutputlist_success(rf, freezer, build_release_with_files):
    workspace = WorkspaceFactory()

    now = timezone.now()

    build_release_with_files(["file1.txt", "file2.txt"], workspace=workspace)
    snapshot1 = SnapshotFactory(
        workspace=workspace,
        published_by=UserFactory(),
        published_at=minutes_ago(now, 3),
    )
    snapshot1.files.set(workspace.files.all())

    build_release_with_files(["file2.txt", "file3.txt"], workspace=workspace)
    snapshot2 = SnapshotFactory(workspace=workspace)
    snapshot2.files.set(workspace.files.all())

    build_release_with_files(["file2.txt", "file3.txt"], workspace=workspace)

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


def test_workspaceoutputlist_without_permission(rf, freezer, build_release_with_files):
    workspace = WorkspaceFactory()

    now = timezone.now()

    build_release_with_files(["file1.txt", "file2.txt"], workspace=workspace)
    snapshot1 = SnapshotFactory(
        workspace=workspace,
        published_by=UserFactory(),
        published_at=minutes_ago(now, 3),
    )
    snapshot1.files.set(workspace.files.all())

    build_release_with_files(["file2.txt", "file3.txt"], workspace=workspace)
    snapshot2 = SnapshotFactory(workspace=workspace, published_at=None)
    snapshot2.files.set(workspace.files.all())

    build_release_with_files(["file2.txt", "file3.txt"], workspace=workspace)

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


def test_workspaceoutputlist_without_snapshots(rf, freezer):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceOutputList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["snapshots"]) == 0
    assert "No outputs have been published" in response.rendered_content


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
