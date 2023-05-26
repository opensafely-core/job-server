import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.authorization import InteractiveReporter
from jobserver.views.reports import ReportPublishRequestCreate

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    ReportFactory,
    UserFactory,
)
from ....fakes import FakeGitHubAPI


def test_reportpublishrequestcreate_get_success(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    response = ReportPublishRequestCreate.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 200


def test_reportpublishrequestcreate_post_success(rf, slack_messages):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    request = rf.post("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ReportPublishRequestCreate.as_view(get_github_api=FakeGitHubAPI)(
        request,
        org_slug=analysis_request.project.org.slug,
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
    assert (
        str(messages[0]) == "Your request to publish this report was successfully sent"
    )

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "co-pilot-support"
    assert report.publish_requests.first().created_by.email in text
    assert report.get_absolute_url() in text


def test_reportpublishrequestcreate_unauthorized(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestCreate.as_view()(
            request,
            org_slug=analysis_request.project.org.slug,
            project_slug=analysis_request.project.slug,
            slug=analysis_request.slug,
        )


def test_reportpublishrequestcreate_unknown_analysis_request(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ReportPublishRequestCreate.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
            slug="",
        )
