import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.models import ReportPublishRequest
from jobserver.utils import set_from_qs
from staff.views.report_publish_requests import (
    ReportPublishRequestApprove,
    ReportPublishRequestDetail,
    ReportPublishRequestList,
    ReportPublishRequestReject,
)

from ....factories import ReportFactory, ReportPublishRequestFactory, UserFactory


def test_reportpublishrequestapprove_success(rf, core_developer, mailoutbox):
    publish_request = ReportPublishRequestFactory(decision_at=None)

    request = rf.post("/")
    request.user = core_developer

    response = ReportPublishRequestApprove.as_view()(request, pk=publish_request.pk)

    assert response.status_code == 302
    assert response.url == publish_request.get_staff_url()

    publish_request.refresh_from_db()
    assert publish_request.decision_at

    m = mailoutbox[0]
    assert m.subject == "Your report has been published"
    assert publish_request.report.get_absolute_url() in m.body


def test_reportpublishrequestapprove_unauthorized(rf):
    publish_request = ReportPublishRequestFactory()

    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestApprove.as_view()(request, pk=publish_request.pk)


def test_reportpublishrequestapprove_unknown_publish_request(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ReportPublishRequestApprove.as_view()(request, pk="0")


def test_reportpublishrequestdetail_success(rf, core_developer):
    publish_request = ReportPublishRequestFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ReportPublishRequestDetail.as_view()(request, pk=publish_request.pk)

    assert response.status_code == 200


def test_reportpublishrequestdetail_unauthorized(rf):
    publish_request = ReportPublishRequestFactory()

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestDetail.as_view()(request, pk=publish_request.pk)


def test_reportpublishrequestdetail_unknown_publish_request(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ReportPublishRequestDetail.as_view()(request, pk="0")


def test_reportpublishrequestlist_filter_by_state_approved(rf, core_developer):
    publish_request = ReportPublishRequestFactory(
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.APPROVED,
    )

    ReportPublishRequestFactory.create_batch(5)

    request = rf.get("?state=approved")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_filter_by_state_pending(rf, core_developer):
    publish_request = ReportPublishRequestFactory()

    ReportPublishRequestFactory.create_batch(
        2,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.APPROVED,
    )
    ReportPublishRequestFactory.create_batch(
        2,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.REJECTED,
    )

    request = rf.get("?state=pending")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_filter_by_state_rejected(rf, core_developer):
    publish_request = ReportPublishRequestFactory(
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.REJECTED,
    )

    ReportPublishRequestFactory.create_batch(5)

    request = rf.get("?state=rejected")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_search_by_report(rf, core_developer):
    report = ReportFactory(title="Database schema report")
    publish_request = ReportPublishRequestFactory(report=report)

    ReportPublishRequestFactory.create_batch(2)

    request = rf.get("/?q=schema")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_search_by_user_created(rf, core_developer):
    user = UserFactory(username="beng")

    publish_request = ReportPublishRequestFactory(
        created_at=timezone.now(), created_by=user
    )

    ReportPublishRequestFactory.create_batch(2)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_search_by_user_decision(rf, core_developer):
    user = UserFactory(username="beng")

    publish_request = ReportPublishRequestFactory(
        decision_at=timezone.now(),
        decision_by=user,
        decision=ReportPublishRequest.Decisions.APPROVED,
    )

    ReportPublishRequestFactory.create_batch(2)

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200


def test_reportpublishrequestlist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestList.as_view()(request)


def test_reportpublishrequestreject_success(rf, core_developer):
    publish_request = ReportPublishRequestFactory(decision_at=None)

    request = rf.post("/")
    request.user = core_developer

    response = ReportPublishRequestReject.as_view()(request, pk=publish_request.pk)

    assert response.status_code == 302
    assert response.url == publish_request.get_staff_url()

    publish_request.refresh_from_db()
    assert publish_request.decision_at
    assert publish_request.decision_by == core_developer
    assert publish_request.decision == ReportPublishRequest.Decisions.REJECTED


def test_reportpublishrequestreject_unauthorized(rf):
    publish_request = ReportPublishRequestFactory()

    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestReject.as_view()(request, pk=publish_request.pk)


def test_reportpublishrequestreject_unknown_publish_request(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ReportPublishRequestReject.as_view()(request, pk="0")