import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.utils import set_from_qs
from staff.views.report_publish_requests import (
    ReportPublishRequestApprove,
    ReportPublishRequestDetail,
    ReportPublishRequestList,
)

from ....factories import ReportFactory, ReportPublishRequestFactory, UserFactory


def test_reportpublishrequestapprove_success(rf, core_developer, mailoutbox):
    publish_request = ReportPublishRequestFactory(approved_at=None)

    request = rf.post("/")
    request.user = core_developer

    response = ReportPublishRequestApprove.as_view()(request, pk=publish_request.pk)

    assert response.status_code == 302
    assert response.url == publish_request.get_staff_url()

    publish_request.refresh_from_db()
    assert publish_request.approved_at

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


def test_reportpublishrequestlist_filter_by_approved_no(rf, core_developer):
    publish_request = ReportPublishRequestFactory()

    ReportPublishRequestFactory.create_batch(
        5, approved_at=timezone.now(), approved_by=UserFactory()
    )

    request = rf.get("?is_approved=no")
    request.user = core_developer

    response = ReportPublishRequestList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {publish_request.pk}


def test_reportpublishrequestlist_filter_by_approved_yes(rf, core_developer):
    publish_request = ReportPublishRequestFactory(
        approved_at=timezone.now(), approved_by=UserFactory()
    )

    ReportPublishRequestFactory.create_batch(5)

    request = rf.get("?is_approved=yes")
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


@pytest.mark.parametrize("user_field", ["approved", "created"])
def test_reportpublishrequestlist_search_by_user(rf, core_developer, user_field):
    user = UserFactory(username="beng")

    publish_request = ReportPublishRequestFactory(
        **{f"{user_field}_at": timezone.now(), f"{user_field}_by": user}
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
