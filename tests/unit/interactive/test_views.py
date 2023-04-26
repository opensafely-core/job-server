import json

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from interactive.dates import END_DATE, START_DATE
from interactive.models import AnalysisRequest
from interactive.views import (
    AnalysisReportUpdate,
    AnalysisRequestCreate,
    AnalysisRequestDetail,
    from_codelist,
)
from jobserver.authorization import InteractiveReporter

from ...factories import (
    AnalysisRequestFactory,
    BackendFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    ReportFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...fakes import FakeOpenCodelistsAPI


def test_analysisrequestcreate_get_success(rf):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=FakeOpenCodelistsAPI
    )(request, org_slug=project.org.slug, project_slug=project.slug)

    assert response.status_code == 200
    assert response.context_data["project"] == project


def test_analysisrequestcreate_post_failure(rf, interactive_repo):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    user = UserFactory()
    WorkspaceFactory(
        project=project, repo=interactive_repo, name=f"{project.slug}-interactive"
    )

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    data = {
        "timeScale": "months",
    }
    request = rf.post("/", data=json.dumps(data), content_type="application/json")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=FakeOpenCodelistsAPI
    )(request, org_slug=project.org.slug, project_slug=project.slug)

    assert response.status_code == 200, response.context_data["form"].errors

    # TODO: check our error response here


def test_analysisrequestcreate_post_success(
    rf, interactive_repo, add_codelist, slack_messages
):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    user = UserFactory()
    WorkspaceFactory(
        project=project, repo=interactive_repo, name=f"{project.slug}-interactive"
    )

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    add_codelist("bennett/event-codelist/event123")
    add_codelist("bennett/medication-codelist/medication123")

    data = {
        "codelistA": {
            "label": "Event Codelist",
            "organisation": "NHSD Primary Care Domain Refsets",
            "value": "bennett/event-codelist/event123",
            "type": "event",
        },
        "codelistB": {
            "label": "Medication Codelist",
            "organisation": "NHSD Primary Care Domain Refsets",
            "value": "bennett/medication-codelist/medication123",
            "type": "medication",
        },
        "demographics": ["age"],
        "filterPopulation": "adults",
        "purpose": "For… science!",
        "title": "Report on science",
        "timeEvent": "before",
        "timeScale": "months",
        "timeValue": "12",
    }
    request = rf.post("/", data=json.dumps(data), content_type="appliation/json")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=FakeOpenCodelistsAPI
    )(request, org_slug=project.org.slug, project_slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors

    analysis_request = AnalysisRequest.objects.first()
    assert response.url == analysis_request.get_absolute_url()

    # check dates were set properly
    analysis_request.template_data["start_date"] == START_DATE
    analysis_request.template_data["end_date"] == END_DATE

    assert len(slack_messages) == 1


def test_analysisrequestcreate_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestCreate.as_view()(
            request, org_slug=project.org.slug, project_slug=project.slug
        )


def test_analysisrequestdetail_success(rf):
    project = ProjectFactory()
    user = UserFactory()
    analysis_request = AnalysisRequestFactory(project=project, created_by=user)

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestDetail.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_with_global_interactivereporter(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    response = AnalysisRequestDetail.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_with_interactivereporter_on_another_project(rf):
    analysis_request = AnalysisRequestFactory()

    user = UserFactory()
    ProjectMembershipFactory(user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            org_slug=analysis_request.project.org.slug,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_analysisrequestdetail_with_no_interactivereporter_role(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            org_slug=analysis_request.project.org.slug,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_from_codelist():
    data = {
        "first": {
            "inner": "value",
        },
        "second": {},
    }
    assert from_codelist(data, "first", "inner") == "value"
    assert from_codelist(data, "second", "inner") == ""


def test_analysisreportupdate_get_success(rf):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="test report title",
        description="test report description",
    )
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.get("/")
    request.user = user

    response = AnalysisReportUpdate.as_view()(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    assert "test report title" in response.rendered_content
    assert "test report description" in response.rendered_content


def test_analysisreportupdate_post_success(rf):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="test report title",
        description="test report description",
    )
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.post("/", {"title": "new title", "description": "new description"})
    request.user = user

    AnalysisReportUpdate.as_view()(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    report.refresh_from_db()
    assert report.title == "new title"
    assert report.description == "new description"


def test_analysisreportupdate_unauthorized(rf):
    project = ProjectFactory()
    user = UserFactory()
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisReportUpdate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )

    request = rf.post("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisReportUpdate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )


def test_analysisreportupdate_no_report(rf):
    project = ProjectFactory()
    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=None,
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        AnalysisReportUpdate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )


def test_analysisreportupdate_post_invalid(rf):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="old title",
        description="old description",
    )
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.post("/", {"title": "", "description": ""})
    request.user = user

    AnalysisReportUpdate.as_view()(
        request,
        org_slug=project.org.slug,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    report.refresh_from_db()
    assert report.title == "old title"
    assert report.description == "old description"
