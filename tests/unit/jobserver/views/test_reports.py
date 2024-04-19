import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import permissions
from jobserver.models import PublishRequest
from jobserver.views.reports import PublishRequestCreate

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
)
from ....fakes import FakeGitHubAPI


def test_publishrequestcreate_get_success(rf, role_factory):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    request = rf.get("/")
    request.user = UserFactory(
        roles=[role_factory(permissions=[permissions.analysis_request_view])]
    )

    response = PublishRequestCreate.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_publishrequestcreate_locked_with_approved_decision(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permissions=[permissions.analysis_request_view])],
    )

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])
    report = ReportFactory(release_file=rfile)
    analysis_request = AnalysisRequestFactory(project=project, report=report)

    request = rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permissions=[permissions.analysis_request_view])]
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

    response = PublishRequestCreate.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200
    assert response.template_name == "interactive/publish_request_create_locked.html"


def test_publishrequestcreate_locked_with_pending_decision(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permissions=[permissions.analysis_request_view])],
    )

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])
    report = ReportFactory(release_file=rfile)
    analysis_request = AnalysisRequestFactory(project=project, report=report)

    PublishRequestFactory(report=report, snapshot=snapshot)

    request = rf.get("/")
    request.user = user

    response = PublishRequestCreate.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200
    assert response.template_name == "interactive/publish_request_create_locked.html"


def test_publishrequestcreate_unlocked_with_rejected_decision(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permissions=[permissions.analysis_request_view])],
    )

    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])
    report = ReportFactory(release_file=rfile)
    analysis_request = AnalysisRequestFactory(project=project, report=report)

    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = user

    response = PublishRequestCreate.as_view()(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200
    assert response.template_name == "interactive/publish_request_create.html"


def test_publishrequestcreate_post_success(rf, slack_messages, role_factory):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    request = rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permissions=[permissions.analysis_request_view])]
    )

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = PublishRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 302
    assert response.url == analysis_request.get_absolute_url()

    analysis_request.refresh_from_db()
    assert analysis_request.publish_request

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "Your request to publish this report was successfully sent to the OpenSAFELY team"
    assert str(messages[0]) == msg

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "co-pilot-support"
    assert report.publish_requests.first().created_by.email in text
    assert report.get_absolute_url() in text


def test_publishrequestcreate_unauthorized(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        PublishRequestCreate.as_view()(
            request,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_publishrequestcreate_unknown_analysis_request(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        PublishRequestCreate.as_view()(
            request,
            project_slug=project.slug,
            slug="",
        )
