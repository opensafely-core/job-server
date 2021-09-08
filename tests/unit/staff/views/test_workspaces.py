import pytest
from django.http import Http404

from staff.views.workspaces import WorkspaceDetail, WorkspaceList

from ....factories import UserFactory, WorkspaceFactory


@pytest.mark.django_db
def test_workspacedetail_success(rf, core_developer):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = core_developer

    response = WorkspaceDetail.as_view()(request, slug=workspace.name)

    assert response.status_code == 200

    assert response.context_data["workspace"] == workspace


@pytest.mark.django_db
def test_workspacedetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        WorkspaceDetail.as_view()(request, slug="test")


@pytest.mark.django_db
def test_workspacedetail_without_core_dev_role(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = WorkspaceDetail.as_view()(request, slug=workspace.name)

    assert response.status_code == 403


@pytest.mark.django_db
def test_workspacelist_search(rf, core_developer):
    WorkspaceFactory(name="ben")
    WorkspaceFactory(repo="ben")
    WorkspaceFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2


@pytest.mark.django_db
def test_workspacelist_success(rf, core_developer):
    WorkspaceFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 5
