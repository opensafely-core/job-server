import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.utils import set_from_qs
from redirects.models import Redirect
from staff.views.workspaces import WorkspaceDetail, WorkspaceEdit, WorkspaceList

from ....factories import (
    OrgFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)


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
    org = OrgFactory()
    old_project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=old_project, purpose="old value")

    new_project = ProjectFactory(org=org)

    data = {
        "purpose": "new value",
        "project": str(new_project.pk),
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = WorkspaceEdit.as_view()(request, slug=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_staff_url()

    workspace.refresh_from_db()
    assert workspace.uses_new_release_flow
    assert workspace.purpose == "new value"

    Redirect.objects.count() == 1
    redirect = Redirect.objects.first()
    assert redirect.workspace == workspace
    assert redirect.old_url == workspace.get_absolute_url().replace(
        workspace.project.get_absolute_url(), old_project.get_absolute_url()
    )


def test_workspaceedit_post_success_when_not_changing_project(rf, core_developer):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)

    data = {
        "purpose": "",
        "project": str(project.pk),
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = WorkspaceEdit.as_view()(request, slug=workspace.name)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == workspace.get_staff_url()

    workspace.refresh_from_db()
    assert workspace.uses_new_release_flow
    assert not workspace.redirects.exists()


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


def test_workspacelist_filter_by_org(rf, core_developer):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    WorkspaceFactory.create_batch(2)

    request = rf.get(f"/?orgs={org.slug}")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["workspace_list"]) == {workspace.pk}


def test_workspacelist_filter_by_project(rf, core_developer):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)
    WorkspaceFactory.create_batch(2)

    request = rf.get(f"/?projects={project.slug}")
    request.user = core_developer

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["workspace_list"]) == {workspace.pk}


def test_workspacelist_search(rf, core_developer):
    WorkspaceFactory(name="ben")
    WorkspaceFactory(repo=RepoFactory(url="ben"))
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
