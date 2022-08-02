import pytest
from django.http import Http404
from django.utils import timezone

from jobserver.views.badges import (
    WorkspaceNumJobs,
    WorkspaceNumPublished,
    WorkspaceNumReleased,
)

from ....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    WorkspaceFactory,
)


def test_worksapcenumjobs_some_jobs(rf):
    workspace = WorkspaceFactory()
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory.create_batch(5, job_request=job_request)

    request = rf.get("/")

    response = WorkspaceNumJobs.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumjobs_no_jobs(rf):
    workspace = WorkspaceFactory()
    JobRequestFactory(workspace=workspace)

    request = rf.get("/")

    response = WorkspaceNumJobs.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumjobs_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceNumJobs.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


def test_workspacenumpublished_with_published_outputs(rf):
    workspace = WorkspaceFactory()

    ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"}),
        workspace=workspace,
    )
    snapshot = SnapshotFactory(workspace=workspace, published_at=timezone.now())
    snapshot.files.set(workspace.files.all())

    request = rf.get("/")

    response = WorkspaceNumPublished.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumpublished_without_published_outputs(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")

    response = WorkspaceNumPublished.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumpublished_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceNumPublished.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )


def test_workspacenumreleased_no_released_files(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")

    response = WorkspaceNumReleased.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumreleased_some_released_files(rf):
    workspace = WorkspaceFactory()

    ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"text", "file2.txt": b"text"}),
        workspace=workspace,
    )

    request = rf.get("/")

    response = WorkspaceNumReleased.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200


def test_workspacenumreleased_unknown_workspace(rf):
    project = ProjectFactory()

    request = rf.get("/")

    with pytest.raises(Http404):
        WorkspaceNumReleased.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            workspace_slug="",
        )
