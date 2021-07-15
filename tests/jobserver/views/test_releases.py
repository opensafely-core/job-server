import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404

from jobserver.authorization import OutputPublisher, ProjectCollaborator
from jobserver.views.releases import (
    ProjectReleaseList,
    ReleaseDetail,
    SnapshotCreate,
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
def test_snapshotcreate_success(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["file1", "file2"]), workspace=workspace)

    assert workspace.snapshots.count() == 0

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    response = SnapshotCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()
    assert workspace.snapshots.count() == 1

    # confirm the snapshot's files match the current workspace files
    output = set(workspace.snapshots.first().files.values_list("pk", flat=True))
    expected = set(workspace.files.values_list("pk", flat=True))
    assert output == expected


@pytest.mark.django_db
def test_snapshotcreate_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    with pytest.raises(Http404):
        SnapshotCreate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


@pytest.mark.django_db
def test_snapshotcreate_with_duplicate_snapshot(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["file1", "file2"]), workspace=workspace)

    # create a Snapshot of the Workspace in its current state
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(workspace.files.all())
    assert workspace.snapshots.count() == 1
    assert workspace.snapshots.first() == snapshot

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = SnapshotCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    # check the snapshot is still the one we created above
    assert workspace.snapshots.count() == 1
    assert workspace.snapshots.first() == snapshot

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    expected = "A release with the current files already exists, please use that one."
    assert str(messages[0]) == expected


@pytest.mark.django_db
def test_snapshotcreate_with_no_outputs(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = SnapshotCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    expected = "There are no outputs to publish for this workspace."
    assert str(messages[0]) == expected


@pytest.mark.django_db
def test_snapshotcreate_without_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SnapshotCreate.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
        )


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
