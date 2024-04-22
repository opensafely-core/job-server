import json

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone
from interactive_templates.dates import END_DATE, START_DATE

from interactive.models import AnalysisRequest
from interactive.views import (
    AnalysisRequestCreate,
    AnalysisRequestDetail,
    ReportEdit,
    from_codelist,
)
from jobserver.authorization import permissions
from jobserver.models import PublishRequest

from ...factories import (
    AnalysisRequestFactory,
    BackendFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...fakes import FakeOpenCodelistsAPI


def test_analysisrequestcreate_get_success(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_create)],
    )

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=FakeOpenCodelistsAPI
    )(request, project_slug=project.slug)

    assert response.status_code == 200
    assert response.context_data["project"] == project


def test_analysisrequestcreate_post_failure(
    rf, interactive_repo, project_membership, role_factory
):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    user = UserFactory()
    WorkspaceFactory(
        project=project, repo=interactive_repo, name=f"{project.slug}-interactive"
    )

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_create)],
    )

    data = {
        "timeScale": "months",
    }
    request = rf.post("/", data=json.dumps(data), content_type="application/json")
    request.user = user

    response = AnalysisRequestCreate.as_view(
        get_opencodelists_api=FakeOpenCodelistsAPI
    )(request, project_slug=project.slug)

    assert response.status_code == 200, response.context_data["form"].errors

    # TODO: check our error response here


def test_analysisrequestcreate_post_success(
    rf, interactive_repo, add_codelist, slack_messages, project_membership, role_factory
):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    user = UserFactory()
    WorkspaceFactory(
        project=project, repo=interactive_repo, name=f"{project.slug}-interactive"
    )

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_create)],
    )
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
    )(request, project_slug=project.slug)

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
        AnalysisRequestCreate.as_view()(request, project_slug=project.slug)


def test_analysisrequestdetail_success(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()
    analysis_request = AnalysisRequestFactory(project=project, created_by=user)

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.release_file_view)],
    )

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_unauthorized(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


def test_analysisrequestdetail_with_global_release_file_view(rf, role_factory):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory(
        roles=[role_factory(permission=permissions.release_file_view)]
    )

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_with_release_file_view_on_another_project(
    rf, project_membership, role_factory
):
    analysis_request = AnalysisRequestFactory()

    user = UserFactory()
    project_membership(
        user=user, roles=[role_factory(permission=permissions.release_file_view)]
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_analysisrequestdetail_with_no_release_file_view(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_analysisrequestdetail_login_redirect_with_different_domain(
    rf, settings, project_membership, role_factory
):
    """
    Test login code with a different LOGIN_URL

    Django's login_required decorator handles the LOGIN_URL being on a
    different domain.  We don't currently support that but we don't want to
    have to remember this one specific view needs updating if we ever did make
    that change so we've copied the contents of the login_required decorator as
    is to maintain continuity with views using the decorator as expected.
    """
    settings.LOGIN_URL = "http://server/login/"

    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.release_file_view)],
    )

    analysis_request = AnalysisRequestFactory(project=project, created_by=user)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 302
    assert response.url == "http://server/login/?next=http%3A//testserver/"


def test_analysisrequestdetail_login_redirect_with_normal_settings(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.release_file_view)],
    )

    analysis_request = AnalysisRequestFactory(project=project, created_by=user)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next=/"


def test_analysisrequestdetail_with_published_report(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.release_file_view)],
    )

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile, title="Testing report")
    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    analysis_request = AnalysisRequestFactory(
        project=project, created_by=user, report=report
    )

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestDetail.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_from_codelist():
    data = {
        "first": {
            "inner": "value",
        },
        "second": {},
    }
    assert from_codelist(data, "first", "inner") == "value"
    assert from_codelist(data, "second", "inner") == ""


def test_reportedit_get_success(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="test report title",
        description="test report description",
    )
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.get("/")
    request.user = user

    response = ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    assert "test report title" in response.rendered_content
    assert "test report description" in response.rendered_content


def test_reportedit_no_report(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=None,
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        ReportEdit.as_view()(
            request,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )


def test_reportedit_post_invalid(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="old title",
        description="old description",
    )
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.post("/", {"title": "", "description": ""})
    request.user = user

    ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    report.refresh_from_db()
    assert report.title == "old title"
    assert report.description == "old description"


def test_reportedit_post_success(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()
    report = ReportFactory(
        title="test report title",
        description="test report description",
    )
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
        report=report,
    )

    request = rf.post("/", {"title": "new title", "description": "new description"})
    request.user = user

    ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    report.refresh_from_db()
    assert report.title == "new title"
    assert report.description == "new description"


def test_reportedit_unauthorized(rf):
    project = ProjectFactory()
    user = UserFactory()
    analysis_request = AnalysisRequestFactory(
        project=project,
        created_by=user,
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        ReportEdit.as_view()(
            request,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )

    request = rf.post("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        ReportEdit.as_view()(
            request,
            project_slug=project.slug,
            slug=analysis_request.slug,
        )


def test_reportedit_locked_with_approved_decision(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile)

    analysis_request = AnalysisRequestFactory(
        created_by=user, project=project, report=report
    )

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )

    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = user

    response = ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200
    assert response.template_name == "interactive/report_edit_locked.html"


def test_reportedit_locked_with_pending_decision(rf, project_membership, role_factory):
    project = ProjectFactory()
    user = UserFactory()

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile)

    analysis_request = AnalysisRequestFactory(
        created_by=user, project=project, report=report
    )

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )
    PublishRequestFactory(report=report, snapshot=snapshot)

    request = rf.get("/")
    request.user = user

    response = ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200
    assert response.template_name == "interactive/report_edit_locked.html"


def test_reportedit_unlocked_with_rejected_decision(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile)

    analysis_request = AnalysisRequestFactory(
        created_by=user, project=project, report=report
    )

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.analysis_request_view)],
    )

    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = user

    response = ReportEdit.as_view()(
        request,
        project_slug=project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200

    # FormView returns a list for template name
    assert response.template_name == ["interactive/report_edit.html"]
