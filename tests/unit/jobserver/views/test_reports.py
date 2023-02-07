import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404

from jobserver.authorization import InteractiveReporter
from jobserver.views.reports import (
    ReportPublishRequestCreate,
    ReportPublishRequestUpdate,
)

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    ReportFactory,
    ReportPublishRequestFactory,
    UserFactory,
)


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


def test_reportpublishrequestcreate_post_success(rf):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    request = rf.post("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ReportPublishRequestCreate.as_view()(
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


def test_reportpublishrequestcreate_with_existing_publish_request(rf):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)
    ReportPublishRequestFactory(report=report)
    assert analysis_request.publish_request

    request = rf.get("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ReportPublishRequestCreate.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        slug=analysis_request.slug,
    )

    assert response.status_code == 302
    assert response.url == analysis_request.get_absolute_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "A request to publish this report already exists"


def test_reportpublishrequestupdate_get_success(rf):
    report = ReportFactory()
    AnalysisRequestFactory(report=report)
    publish_request = ReportPublishRequestFactory(report=report)

    request = rf.get("/")
    request.user = UserFactory()

    response = ReportPublishRequestUpdate.as_view()(request, pk=publish_request.pk)

    assert response.status_code == 200


def test_reportpublishrequestupdate_post_success(rf):
    report = ReportFactory()
    AnalysisRequestFactory(report=report)
    publish_request = ReportPublishRequestFactory(report=report)

    request = rf.post("/")
    request.user = UserFactory()

    response = ReportPublishRequestUpdate.as_view()(request, pk=publish_request.pk)
    assert response.status_code == 302
    assert response.url == publish_request.get_absolute_url()

    publish_request.refresh_from_db()
    assert publish_request.approved_at
