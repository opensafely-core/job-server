import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse

from redirects.models import Redirect
from staff.views.redirects import RedirectDelete, RedirectDetail, RedirectList

from ....factories import (
    AnalysisRequestFactory,
    OrgFactory,
    ProjectFactory,
    RedirectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_redirectdelete_success(rf, core_developer):
    workspace = WorkspaceFactory()
    redirect = RedirectFactory(workspace=workspace)

    request = rf.post("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = RedirectDelete.as_view()(request, pk=redirect.pk)

    assert response.status_code == 302
    assert response.url == reverse("staff:redirect-list")

    assert not Redirect.objects.filter(pk=redirect.pk).exists()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == f"Deleted redirect for Workspace: {workspace.name}"


def test_redirectdelete_with_unknown_redirect(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        RedirectDelete.as_view()(request, pk="0")


def test_redirectdelete_without_core_dev_role(rf):
    redirect = RedirectFactory(workspace=WorkspaceFactory())

    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RedirectDelete.as_view()(request, pk=redirect.pk)


def test_redirectedetail_success(rf, core_developer):
    redirect = RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get("/")
    request.user = core_developer

    response = RedirectDetail.as_view()(request, pk=redirect.pk)

    assert response.status_code == 200
    assert response.context_data["object"] == redirect


def test_redirectedetail_with_unknown_redirect(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        RedirectDetail.as_view()(request, pk="0")


def test_redirectedetail_without_core_dev_role(rf):
    redirect = RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RedirectDetail.as_view()(request, pk=redirect.pk)


def test_redirectlist_filter_by_object_type(rf, core_developer):
    project_redirects = RedirectFactory.create_batch(3, project=ProjectFactory())
    workspace_redirects = RedirectFactory.create_batch(3, workspace=WorkspaceFactory())

    request = rf.get("/?type=project")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == set(project_redirects)

    request = rf.get("/?type=workspace")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == set(workspace_redirects)


def test_redirectlist_search_by_analysis_request(rf, core_developer):
    analysis_request = AnalysisRequestFactory()
    redirect = RedirectFactory(analysis_request=analysis_request)

    RedirectFactory(org=OrgFactory())
    RedirectFactory(project=ProjectFactory())
    RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get(f"/?q={analysis_request.title}")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_jobrequestlist_search_by_fullname(rf, core_developer):
    org = OrgFactory()
    user = UserFactory(fullname="Ben Goldacre")
    redirect = RedirectFactory(org=org, created_by=user)

    RedirectFactory.create_batch(5, org=org)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_search_by_old_url(rf, core_developer):
    org = OrgFactory()
    redirect = RedirectFactory(org=org, old_url="/test/foo/bar/")

    RedirectFactory.create_batch(5, org=org)

    request = rf.get("/?q=foo")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_search_by_org(rf, core_developer):
    org = OrgFactory()
    redirect = RedirectFactory(org=org)

    RedirectFactory(analysis_request=AnalysisRequestFactory())
    RedirectFactory(project=ProjectFactory())
    RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get(f"/?q={org.name}")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_search_by_project(rf, core_developer):
    project = ProjectFactory()
    redirect = RedirectFactory(project=project)

    RedirectFactory(analysis_request=AnalysisRequestFactory())
    RedirectFactory(org=OrgFactory())
    RedirectFactory(project=ProjectFactory())
    RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get(f"/?q={project.name}")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_search_by_username(rf, core_developer):
    org = OrgFactory()
    user = UserFactory(username="beng")
    redirect = RedirectFactory(org=org, created_by=user)

    RedirectFactory.create_batch(5, org=org)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_search_by_workspace(rf, core_developer):
    project = ProjectFactory()
    redirect = RedirectFactory(project=project)

    RedirectFactory(analysis_request=AnalysisRequestFactory())
    RedirectFactory(org=OrgFactory())
    RedirectFactory(workspace=WorkspaceFactory())

    request = rf.get(f"/?q={project.name}")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {redirect}


def test_redirectlist_success(rf, core_developer):
    RedirectFactory.create_batch(5, project=ProjectFactory())

    request = rf.get("/")
    request.user = core_developer

    response = RedirectList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 5


def test_redirectlist_without_core_dev_role(rf):
    RedirectFactory.create_batch(5, project=ProjectFactory())

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RedirectList.as_view()(request)
