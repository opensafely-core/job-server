import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.utils import set_from_qs
from staff.views.analysis_requests import AnalysisRequestDetail, AnalysisRequestList

from ....factories import AnalysisRequestFactory, ProjectFactory, UserFactory


def test_analysisrequestdetail_success(rf, core_developer):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = core_developer

    response = AnalysisRequestDetail.as_view()(request, pk=analysis_request.pk)

    assert response.status_code == 200


def test_analysisrequestdetail_unauthorized(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(request, pk=analysis_request.pk)


def test_analysisrequestdetail_unknown_analysis_request(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        AnalysisRequestDetail.as_view()(request, pk="")


def test_analysisrequestlist_filter_by_project(rf, core_developer):
    project = ProjectFactory()
    ar1 = AnalysisRequestFactory(project=project)
    AnalysisRequestFactory()
    ar3 = AnalysisRequestFactory(project=project)

    request = rf.get(f"/?project={project.slug}")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {ar1.pk, ar3.pk}


def test_analysisrequestlist_filter_by_user(rf, core_developer):
    user = UserFactory()
    ar1 = AnalysisRequestFactory(created_by=user)
    AnalysisRequestFactory.create_batch(2)

    request = rf.get(f"/?user={user.username}")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {ar1.pk}


def test_analysisrequestlist_search(rf, core_developer):
    ar1 = AnalysisRequestFactory(created_by=UserFactory(username="beng"))
    AnalysisRequestFactory()

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {ar1.pk}


def test_analysisrequestlist_success(rf, core_developer):
    AnalysisRequestFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 5


def test_analysisrequestlist_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestList.as_view()(request)
