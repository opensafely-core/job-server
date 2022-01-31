import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from staff.views.workspaces import WorkspaceDetail, WorkspaceEdit, WorkspaceList

from ....factories import UserFactory, WorkspaceFactory


def test_workspacedetail_success(rf, core_developer):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = core_developer

    response = WorkspaceDetail.as_view()(request, slug=workspace.name)

    assert response.status_code == 200

    assert response.context_data["workspace"] == workspace


def test_workspacedetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        WorkspaceDetail.as_view()(request, slug="test")


def test_workspacedetail_without_core_dev_role(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        WorkspaceDetail.as_view()(request, slug=workspace.name)


def test_workspaceedit_get_success(rf, core_developer):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = core_developer

    response = WorkspaceEdit.as_view()(request, slug=workspace.name)

    assert response.status_code == 200
    assert workspace.name in response.rendered_content


def test_workspaceedit_post_success(rf, core_developer):
    workspace = WorkspaceFactory(uses_new_release_flow=False)

    request = rf.post("/", {"uses_new_release_flow": True})
    request.user = core_developer

    response = WorkspaceEdit.as_view()(request, slug=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_staff_url()

    workspace.refresh_from_db()
    assert workspace.uses_new_release_flow


def test_workspaceedit_unauthorized(rf):
    workspace = WorkspaceFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        WorkspaceEdit.as_view()(request, slug=workspace.name)


def test_workspaceedit_unknown_workspace(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        WorkspaceEdit.as_view()(request, slug="")


def test_workspacelist_search(rf, core_developer):
    WorkspaceFactory(name="ben")
    WorkspaceFactory(repo="ben")
    WorkspaceFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2


def test_workspacelist_success(rf, core_developer):
    WorkspaceFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 5
