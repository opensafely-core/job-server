import pytest
from django.http import Http404

from jobserver.authorization import ProjectCollaborator
from jobserver.views.releases import (
    ProjectReleaseList,
    ReleaseDetail,
    SnapshotDetail,
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
def test_snapshotdetail_success(rf):
    snapshot = SnapshotFactory()

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
def test_snapshotdetail_without_permission(rf):
    snapshot = SnapshotFactory()

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
def test_workspacereleaselist_success(rf):
    workspace = WorkspaceFactory()
    request = rf.get("/")

    response = WorkspaceReleaseList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200
    assert response.context_data["workspace"] == workspace


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
