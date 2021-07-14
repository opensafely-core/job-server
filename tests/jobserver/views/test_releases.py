import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404

from jobserver.authorization import OutputPublisher
from jobserver.views.releases import (
    ProjectReleaseList,
    PublicReleaseCreate,
    ReleaseDetail,
    WorkspaceReleaseList,
)

from ...factories import (
    OrgFactory,
    ProjectFactory,
    PublicReleaseFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
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
def test_publicreleasecreate_success(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["file1", "file2"]), workspace=workspace)

    assert workspace.public_releases.count() == 0

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    response = PublicReleaseCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()
    assert workspace.public_releases.count() == 1

    # confirm the public release's files match the current workspace files
    output = set(workspace.public_releases.first().files.values_list("pk", flat=True))
    expected = set(workspace.files.values_list("pk", flat=True))
    assert output == expected


@pytest.mark.django_db
def test_publicreleasecreate_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    with pytest.raises(Http404):
        PublicReleaseCreate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


@pytest.mark.django_db
def test_publicreleasecreate_with_duplicate_public_release(rf):
    workspace = WorkspaceFactory()
    ReleaseFactory(ReleaseUploadsFactory(["file1", "file2"]), workspace=workspace)

    # create a PublicRelease of the Workspace in its current state
    public_release = PublicReleaseFactory(workspace=workspace)
    public_release.files.set(workspace.files.all())
    assert workspace.public_releases.count() == 1
    assert workspace.public_releases.first() == public_release

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = PublicReleaseCreate.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 302
    assert response.url == workspace.get_absolute_url()

    workspace.refresh_from_db()

    # check the public release is still the one we created above
    assert workspace.public_releases.count() == 1
    assert workspace.public_releases.first() == public_release

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    expected = "A release with the current files already exists, please use that one."
    assert str(messages[0]) == expected


@pytest.mark.django_db
def test_publicreleasecreate_with_no_outputs(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = PublicReleaseCreate.as_view()(
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
def test_publicreleasecreate_without_permission(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        PublicReleaseCreate.as_view()(
            request,
            org_slug=workspace.project.org.slug,
            project_slug=workspace.project.slug,
            workspace_slug=workspace.name,
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
