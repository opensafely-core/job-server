import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.utils import set_from_qs
from staff.views.job_requests import JobRequestDetail, JobRequestList

from ....factories import (
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_jobrequestdetail_success(rf, core_developer):
    job_request = JobRequestFactory()

    request = rf.get("/")
    request.user = core_developer

    response = JobRequestDetail.as_view()(request, pk=job_request.pk)

    assert response.status_code == 200


def test_jobrequestdetail_unauthorized(rf):
    job_request = JobRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        JobRequestDetail.as_view()(request, pk=job_request.pk)


def test_jobrequestdetail_unknown_job_request(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        JobRequestDetail.as_view()(request, pk=0)


def test_jobrequestlist_filter_by_workspace(rf, core_developer):
    JobRequestFactory.create_batch(5)

    workspace = WorkspaceFactory(name="workspace-testing-research")
    job_request = JobRequestFactory(workspace=workspace)

    request = rf.get(f"/?workspace={workspace.name}")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_fullname(rf, core_developer):
    JobRequestFactory.create_batch(5)

    user = UserFactory(fullname="Ben Goldacre")
    job_request = JobRequestFactory(created_by=user)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_identifier(rf, core_developer):
    JobRequestFactory.create_batch(5)

    job_request = JobRequestFactory(identifier="1234abcd")

    request = rf.get("/?q=1234abcd")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}

    request = rf.get("/?q=34ab")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_org(rf, core_developer):
    JobRequestFactory.create_batch(5)

    org = OrgFactory(name="University of Testing")
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(workspace=workspace)

    request = rf.get("/?q=university")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_pk(rf, core_developer):
    JobRequestFactory.create_batch(5)

    job_request = JobRequestFactory()

    request = rf.get(f"/?q={job_request.pk}")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_project(rf, core_developer):
    JobRequestFactory.create_batch(5)

    project = ProjectFactory(name="A Very Important Project")
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(workspace=workspace)

    request = rf.get("/?q=important")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_username(rf, core_developer):
    JobRequestFactory.create_batch(5)

    user = UserFactory(username="beng")
    job_request = JobRequestFactory(created_by=user)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_search_by_workspace(rf, core_developer):
    JobRequestFactory.create_batch(5)

    workspace = WorkspaceFactory(name="workspace-testing-research")
    job_request = JobRequestFactory(workspace=workspace)

    request = rf.get("/?q=research")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 1
    assert set_from_qs(response.context_data["object_list"]) == {job_request.pk}


def test_jobrequestlist_success(rf, core_developer):
    JobRequestFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = JobRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 5


def test_jobrequestlist_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        JobRequestList.as_view()(request)
