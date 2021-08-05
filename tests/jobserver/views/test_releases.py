import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import OutputPublisher, ProjectCollaborator
from jobserver.views.releases import (
    ProjectReleaseList,
    ReleaseDetail,
    ReleaseDownload,
    SnapshotDetail,
    SnapshotDownload,
    WorkspaceReleaseList,
)

from ...factories import (
    OrgFactory,
    ProjectFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.mark.django_db
def test_projectreleaselist_success(rf):
    project = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project)
    workspace2 = WorkspaceFactory(project=project)

    ReleaseFactory(
        ReleaseUploadsFactory(["test1", "test2"]),
        workspace=workspace1,
    )
    ReleaseFactory(
        ReleaseUploadsFactory(["test3", "test4"]),
        workspace=workspace2,
    )

    request = rf.get("/")

    response = ProjectReleaseList.as_view()(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
    )

    assert response.status_code == 200

    assert response.context_data["project"] == project
    assert len(response.context_data["object_list"]) == 2


@pytest.mark.django_db
def test_projectreleaselist_unknown_workspace(rf):
    org = OrgFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        ProjectReleaseList.as_view()(
            request,
            org_slug=org.slug,
            project_slug="",
        )


@pytest.mark.django_db
def test_releasedetail_no_path_success(rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]))

    request = rf.get("/")

    response = ReleaseDetail.as_view()(
        request,
        org_slug=release.workspace.project.org.slug,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.id,
        path="",
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_releasedetail_unknown_release(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    with pytest.raises(Http404):
        ReleaseDetail.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk="",
        )


@pytest.mark.django_db
def test_releasedetail_with_path_success(rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]))

    request = rf.get("/")

    response = ReleaseDetail.as_view()(
        request,
        org_slug=release.workspace.project.org.slug,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.id,
        path="test123/some/path",
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_releasedetail_without_files(rf):
    release = ReleaseFactory(uploads=[], uploaded=False)

    request = rf.get("/")

    with pytest.raises(Http404):
        ReleaseDetail.as_view()(
            request,
            org_slug=release.workspace.project.org.slug,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.id,
        )


@pytest.mark.django_db
def test_releasedownload_release_with_no_files(rf):
    release = ReleaseFactory(uploads=[], uploaded=False)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            org_slug=release.workspace.project.org.slug,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
        )


@pytest.mark.django_db
def test_releasedownload_success(rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]))

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = ReleaseDownload.as_view()(
        request,
        org_slug=release.workspace.project.org.slug,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_releasedownload_unknown_release(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk="",
        )


@pytest.mark.django_db
def test_releasedownload_without_permission(rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]))

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            org_slug=release.workspace.project.org.slug,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
        )


@pytest.mark.django_db
def test_snapshotdetail_published_logged_out(rf):
    snapshot = SnapshotFactory(published_at=timezone.now())

    request = rf.get("/")
    request.user = AnonymousUser()

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdetail_published_with_permission(rf):
    snapshot = SnapshotFactory(published_at=timezone.now())

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdetail_published_without_permission(rf):
    snapshot = SnapshotFactory(published_at=timezone.now())

    request = rf.get("/")
    request.user = UserFactory()

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdetail_unpublished_with_permission_to_publish(rf):
    snapshot = SnapshotFactory(published_at=None)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputPublisher, ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.context_data["publish_url"] == snapshot.get_publish_api_url()


@pytest.mark.django_db
def test_snapshotdetail_unpublished_without_permission_to_publish(rf):
    snapshot = SnapshotFactory(published_at=None)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200
    assert "publish_url" not in response.context_data


@pytest.mark.django_db
def test_snapshotdetail_unpublished_with_permission_to_view(rf):
    snapshot = SnapshotFactory(published_at=None)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdetail_unpublished_without_permission_to_view(rf):
    snapshot = SnapshotFactory(published_at=None)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SnapshotDetail.as_view()(
            request,
            org_slug=snapshot.workspace.project.org.slug,
            project_slug=snapshot.workspace.project.slug,
            workspace_slug=snapshot.workspace.name,
            pk=snapshot.pk,
        )


@pytest.mark.django_db
def test_snapshotdetail_unknown_snapshot(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        SnapshotDetail.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=0,
        )


@pytest.mark.django_db
def test_snapshotdownload_published_with_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace, published_at=timezone.now())
    snapshot.files.set(workspace.files.all())

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDownload.as_view()(
        request,
        org_slug=snapshot.workspace.project.org.slug,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdownload_published_without_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace, published_at=timezone.now())
    snapshot.files.set(workspace.files.all())

    request = rf.get("/")
    request.user = UserFactory()

    response = SnapshotDownload.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdownload_unknown_snapshot(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=0,
        )


@pytest.mark.django_db
def test_snapshotdownload_unpublished_with_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace, published_at=None)
    snapshot.files.set(workspace.files.all())

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDownload.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_snapshotdownload_unpublished_without_permission(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace, published_at=None)
    snapshot.files.set(workspace.files.all())

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=snapshot.pk,
        )


@pytest.mark.django_db
def test_snapshotdownload_with_no_files(rf):
    snapshot = SnapshotFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            org_slug=snapshot.workspace.project.org.slug,
            project_slug=snapshot.workspace.project.slug,
            workspace_slug=snapshot.workspace.name,
            pk=snapshot.pk,
        )


@pytest.mark.django_db
def test_workspacereleaselist_authenticated(rf):
    workspace = WorkspaceFactory()
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceReleaseList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["workspace"] == workspace
    assert len(response.context_data["releases"]) == 1
    assert response.context_data["releases"][0] == release

    assert response.context_data["user_can_view_all_files"]
    assert "Latest outputs" in response.rendered_content


@pytest.mark.django_db
def test_workspacereleaselist_no_releases(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        WorkspaceReleaseList.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


@pytest.mark.django_db
def test_workspacereleaselist_unauthenticated(rf):
    workspace = WorkspaceFactory()
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]), workspace=workspace)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = WorkspaceReleaseList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["workspace"] == workspace
    assert len(response.context_data["releases"]) == 1
    assert response.context_data["releases"][0] == release

    assert "Latest outputs" not in response.rendered_content


@pytest.mark.django_db
def test_workspacereleaselist_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceReleaseList.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )
