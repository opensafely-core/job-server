from datetime import timedelta

import pytest
from django.http import Http404
from django.utils import timezone

from jobserver.views.releases import Releases, WorkspaceReleaseList

from ...factories import OrgFactory, ProjectFactory, ReleaseFactory, WorkspaceFactory


@pytest.mark.django_db
def test_releases_success(rf):
    project = ProjectFactory()

    request = rf.get("/")

    response = Releases.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_releases_unknown_project(rf):
    org = OrgFactory()

    request = rf.get("/")
    with pytest.raises(Http404):
        Releases.as_view()(request, org_slug=org.slug, project_slug="")


@pytest.mark.django_db
def test_workspacereleaselist_success(rf, freezer):
    workspace = WorkspaceFactory()
    release1 = ReleaseFactory(
        workspace=workspace,
        files=["test1", "test2"],
        created_at=timezone.now() - timedelta(minutes=3),
    )
    release2 = ReleaseFactory(
        workspace=workspace,
        files=["test2", "test3"],
        created_at=timezone.now() - timedelta(minutes=2),
    )
    release3 = ReleaseFactory(
        workspace=workspace,
        files=["test3", "test4"],
        created_at=timezone.now() - timedelta(minutes=1),
    )

    request = rf.get("/")

    response = WorkspaceReleaseList.as_view()(
        request,
        org_slug=workspace.project.org.slug,
        project_slug=workspace.project.slug,
        workspace_slug=workspace.name,
    )

    assert response.status_code == 200

    assert response.context_data["workspace"] == workspace

    assert response.context_data["files"][0].name == "test1"
    assert response.context_data["files"][0].release == release1
    assert response.context_data["files"][1].name == "test2"
    assert response.context_data["files"][1].release == release2
    assert response.context_data["files"][2].name == "test3"
    assert response.context_data["files"][2].release == release3
    assert response.context_data["files"][3].name == "test4"
    assert response.context_data["files"][3].release == release3


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
