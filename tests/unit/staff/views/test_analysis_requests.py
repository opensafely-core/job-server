import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.utils import set_from_qs
from staff.views.analysis_requests import (
    AnalysisRequestDetail,
    AnalysisRequestList,
    AnalysisRequestResubmit,
)
from tests.fakes import FakeGitHubAPI

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_analysisrequestdetail_success_with_publish_requests(rf, core_developer):
    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.add(rfile)

    report = ReportFactory(release_file=rfile)

    PublishRequestFactory.create_batch(2, report=report, snapshot=snapshot)
    analysis_request = AnalysisRequestFactory(report=report)

    request = rf.get("/")
    request.user = core_developer

    response = AnalysisRequestDetail.as_view()(request, slug=analysis_request.slug)

    assert response.status_code == 200
    assert len(response.context_data["publish_requests"]) == 2


def test_analysisrequestdetail_success_without_publish_requests(rf, core_developer):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = core_developer

    response = AnalysisRequestDetail.as_view()(request, slug=analysis_request.slug)

    assert response.status_code == 200
    assert response.context_data["publish_requests"] == []


def test_analysisrequestdetail_unauthorized(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(request, slug=analysis_request.slug)


def test_analysisrequestdetail_unknown_analysis_request(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        AnalysisRequestDetail.as_view()(request, slug="")


def test_analysisrequestresubmit_success(rf, core_developer):
    project = ProjectFactory()
    analysis_request = AnalysisRequestFactory(project=project)
    WorkspaceFactory(name=project.interactive_slug, project=project)

    request = rf.post("/")
    request.user = core_developer

    AnalysisRequestResubmit.as_view(get_github_api=FakeGitHubAPI)(
        request, slug=analysis_request.id
    )


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


def test_analysisrequestlist_filter_by_report_no(rf, core_developer):
    ar1 = AnalysisRequestFactory()
    AnalysisRequestFactory(report=ReportFactory())
    ar3 = AnalysisRequestFactory()

    request = rf.get("/?has_report=no")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {ar1.pk, ar3.pk}


def test_analysisrequestlist_filter_by_report_yes(rf, core_developer):
    ar1 = AnalysisRequestFactory(report=ReportFactory())
    AnalysisRequestFactory.create_batch(2)

    request = rf.get("/?has_report=yes")
    request.user = core_developer

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {ar1.pk}


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
