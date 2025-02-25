import json

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from interactive.views import (
    AnalysisRequestCreate,
    AnalysisRequestDetail,
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


def test_analysisrequestcreate_get_denied(rf, project_membership):
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
    )

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisRequestCreate.as_view(get_opencodelists_api=FakeOpenCodelistsAPI)(
            request, project_slug=project.slug
        )


def test_analysisrequestcreate_post_denied(
    rf, interactive_repo, add_codelist, slack_messages, project_membership
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
    )

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

    with pytest.raises(PermissionDenied):
        AnalysisRequestCreate.as_view(get_opencodelists_api=FakeOpenCodelistsAPI)(
            request, project_slug=project.slug
        )


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
