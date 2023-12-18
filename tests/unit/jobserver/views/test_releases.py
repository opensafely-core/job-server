import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import OutputChecker, OutputPublisher, ProjectCollaborator
from jobserver.models import PublishRequest, ReleaseFile
from jobserver.views.releases import (
    ProjectReleaseList,
    PublishedSnapshotFile,
    ReleaseDetail,
    ReleaseDownload,
    ReleaseFileDelete,
    SnapshotDetail,
    SnapshotDownload,
    WorkspaceReleaseList,
)

from ....factories import (
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_projectreleaselist_no_releases(rf):
    project = ProjectFactory()
    WorkspaceFactory.create_batch(3, project=project)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ProjectReleaseList.as_view()(request, project_slug=project.slug)


def test_projectreleaselist_success(rf, build_release):
    project = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project)
    workspace2 = WorkspaceFactory(project=project)

    r1 = build_release(["test1", "test2"], workspace=workspace1)
    build_release(["test3", "test4"], workspace=workspace2)

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectReleaseList.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200

    assert response.context_data["project"] == project
    assert len(response.context_data["releases"]) == 2
    assert f"Files released by {r1.created_by.name}" in response.rendered_content
    assert f"{r1.backend.name}" in response.rendered_content


def test_projectreleaselist_unknown_workspace(rf):
    request = rf.get("/")

    with pytest.raises(Http404):
        ProjectReleaseList.as_view()(request, project_slug="")


def test_projectreleaselist_with_delete_permission(rf, build_release_with_files):
    project = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project)
    workspace2 = WorkspaceFactory(project=project)

    build_release_with_files(("test1", "test2"), workspace=workspace1)
    build_release_with_files(["test3", "test4"], workspace=workspace2)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputChecker, ProjectCollaborator])

    response = ProjectReleaseList.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200

    assert response.context_data["project"] == project
    assert len(response.context_data["releases"]) == 2

    assert response.context_data["user_can_delete_files"]
    assert "Delete" in response.rendered_content


def test_publishedsnapshotfile_success(rf, release):
    rfile = release.files.first()
    snapshot = SnapshotFactory()
    snapshot.files.add(rfile)
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    rfile = release.files.first()

    request = rf.get("/")
    request.user = AnonymousUser()

    response = PublishedSnapshotFile.as_view()(
        request,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        file_id=rfile.id,
    )

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == rfile.absolute_path().read_bytes()
    assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert response.headers["Last-Modified"]


def test_publishedsnapshotfile_with_unknown_release_file(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        PublishedSnapshotFile.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            file_id="",
        )


def test_publishedsnapshotfile_with_unpublished_release_file(rf, release):
    snapshot = SnapshotFactory()
    snapshot.files.set(release.files.all())

    rfile = release.files.first()

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        PublishedSnapshotFile.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            file_id=rfile.id,
        )


def test_releasedetail_unknown_release(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    with pytest.raises(Http404):
        ReleaseDetail.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk="",
        )


def test_releasedetail_with_path_success(rf, release):
    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = ReleaseDetail.as_view()(
        request,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.id,
        path="test123/some/path",
    )

    assert response.status_code == 200


def test_releasedetail_without_permission(rf, release):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReleaseDetail.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.id,
        )


def test_releasedetail_without_files(rf):
    release = ReleaseFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ReleaseDetail.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.id,
        )


def test_releasedownload_release_with_no_files(rf):
    release = ReleaseFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
        )


def test_releasedownload_success(rf, release):
    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = ReleaseDownload.as_view()(
        request,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.pk,
    )

    assert response.status_code == 200


def test_releasedownload_unknown_release(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk="",
        )


def test_releasedownload_without_permission(rf, release):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReleaseDownload.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
        )


def test_releasefiledelete_deleted_file(rf):
    rfile = ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=UserFactory())

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputChecker])

    with pytest.raises(Http404):
        ReleaseFileDelete.as_view()(
            request,
            project_slug=rfile.release.workspace.project.slug,
            workspace_slug=rfile.release.workspace.name,
            pk=rfile.release.pk,
            release_file_id=rfile.pk,
        )


def test_releasefiledelete_no_file_on_disk(rf):
    rfile = ReleaseFileFactory()

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputChecker])

    with pytest.raises(Http404):
        ReleaseFileDelete.as_view()(
            request,
            project_slug=rfile.release.workspace.project.slug,
            workspace_slug=rfile.release.workspace.name,
            pk=rfile.release.pk,
            release_file_id=rfile.pk,
        )


def test_releasefiledelete_success(rf, time_machine, release):
    now = timezone.now()
    time_machine.move_to(now, tick=False)

    rfile = release.files.first()
    user = UserFactory(roles=[OutputChecker])

    request = rf.post("/")
    request.user = user

    response = ReleaseFileDelete.as_view()(
        request,
        project_slug=release.workspace.project.slug,
        workspace_slug=release.workspace.name,
        pk=release.pk,
        release_file_id=rfile.pk,
    )

    assert response.status_code == 302
    assert response.url == rfile.release.workspace.get_releases_url()

    rfile.refresh_from_db()
    assert not rfile.absolute_path().exists()
    assert rfile.deleted_by == user
    assert rfile.deleted_at == now


def test_releasefiledelete_unknown_release_file(rf):
    release = ReleaseFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReleaseFileDelete.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
            release_file_id="",
        )


def test_releasefiledelete_without_permission(rf, release):
    rfile = release.files.first()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReleaseFileDelete.as_view()(
            request,
            project_slug=release.workspace.project.slug,
            workspace_slug=release.workspace.name,
            pk=release.pk,
            release_file_id=rfile.pk,
        )


def test_snapshotdetail_published_logged_out(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    request = rf.get("/")
    request.user = AnonymousUser()

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdetail_published_with_permission(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdetail_published_without_permission(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdetail_unpublished_with_permission_to_publish(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputPublisher, ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.context_data["publish_url"] == snapshot.get_publish_api_url()


def test_snapshotdetail_unpublished_without_permission_to_publish(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200
    assert "publish_url" not in response.context_data


def test_snapshotdetail_unpublished_with_permission_to_view(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDetail.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdetail_unpublished_without_permission_to_view(rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SnapshotDetail.as_view()(
            request,
            project_slug=snapshot.workspace.project.slug,
            workspace_slug=snapshot.workspace.name,
            pk=snapshot.pk,
        )


def test_snapshotdetail_unknown_snapshot(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        SnapshotDetail.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=0,
        )


def test_snapshotdownload_published_with_permission(rf, release):
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDownload.as_view()(
        request,
        project_slug=snapshot.workspace.project.slug,
        workspace_slug=snapshot.workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdownload_published_without_permission(rf, release):
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    PublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    request = rf.get("/")
    request.user = UserFactory()

    response = SnapshotDownload.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdownload_unknown_snapshot(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=0,
        )


def test_snapshotdownload_unpublished_with_permission(rf, release):
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotDownload.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
        pk=snapshot.pk,
    )

    assert response.status_code == 200


def test_snapshotdownload_unpublished_without_permission(rf, release):
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    PublishRequestFactory(snapshot=snapshot)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
            pk=snapshot.pk,
        )


def test_snapshotdownload_with_no_files(rf):
    snapshot = SnapshotFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        SnapshotDownload.as_view()(
            request,
            project_slug=snapshot.workspace.project.slug,
            workspace_slug=snapshot.workspace.name,
            pk=snapshot.pk,
        )


def test_workspacereleaselist_authenticated_to_view_not_delete(
    rf, build_release_with_files
):
    workspace = WorkspaceFactory()
    release = build_release_with_files(["test1"], workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = WorkspaceReleaseList.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["workspace"] == workspace
    assert len(response.context_data["releases"]) == 1

    assert all(r["can_view_files"] for r in response.context_data["releases"])
    assert "All outputs" in response.rendered_content

    assert not response.context_data["user_can_delete_files"]
    assert "Delete" not in response.rendered_content
    assert (
        f"Files released by {release.created_by.name} from {release.backend.name}"
        in response.rendered_content
    )


def test_workspacereleaselist_authenticated_to_view_and_delete(
    rf, build_release_with_files
):
    workspace = WorkspaceFactory()
    build_release_with_files(["test1"], workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputChecker, ProjectCollaborator])

    response = WorkspaceReleaseList.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert len(response.context_data["releases"]) == 1

    assert all(r["can_view_files"] for r in response.context_data["releases"])
    assert "All outputs" in response.rendered_content

    assert response.context_data["user_can_delete_files"]
    assert "Delete" in response.rendered_content


def test_workspacereleaselist_no_releases(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    with pytest.raises(Http404):
        WorkspaceReleaseList.as_view()(
            request,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


def test_workspacereleaselist_unauthenticated(rf, build_release):
    workspace = WorkspaceFactory()
    build_release(["test1"], workspace=workspace)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = WorkspaceReleaseList.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["workspace"] == workspace
    assert len(response.context_data["releases"]) == 1

    assert "All outputs" not in response.rendered_content


def test_workspacereleaselist_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceReleaseList.as_view()(
            request,
            project_slug=project.slug,
            workspace_slug="",
        )


def test_workspacereleaselist_build_files_for_latest(rf, build_release):
    workspace = WorkspaceFactory()
    build_release(["test1"], workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputChecker, ProjectCollaborator])

    response = WorkspaceReleaseList.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["latest_release"]["id"] == "latest"
    files = response.context_data["latest_release"]["files"]
    assert all(f["detail_url"].__func__ == ReleaseFile.get_latest_url for f in files)


def test_workspacereleaselist_build_files_for_releases(rf, build_release):
    workspace = WorkspaceFactory()
    build_release(["test1"], workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory(roles=[OutputChecker, ProjectCollaborator])

    response = WorkspaceReleaseList.as_view()(
        request,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    files = response.context_data["releases"][0]["files"]
    assert all(f["detail_url"].__func__ == ReleaseFile.get_absolute_url for f in files)
