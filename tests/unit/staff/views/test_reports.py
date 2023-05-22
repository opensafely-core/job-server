import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.models import ReportPublishRequest
from jobserver.utils import set_from_qs
from staff.views.reports import (
    ReportDetail,
    ReportList,
    ReportPublishRequestApprove,
    ReportPublishRequestReject,
)

from ....factories import (
    OrgFactory,
    ProjectFactory,
    ReleaseFileFactory,
    ReportFactory,
    ReportPublishRequestFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_reportdetail_success(rf, core_developer):
    report = ReportFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ReportDetail.as_view()(request, pk=report.pk)

    assert response.status_code == 200


def test_reportdetail_unauthorized(rf):
    report = ReportFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ReportDetail.as_view()(request, pk=report.pk)


def test_reportlist_success(rf, core_developer):
    ReportFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 5


def test_reportlist_filter_by_state_approved(rf, core_developer):
    report = ReportFactory()
    ReportPublishRequestFactory(
        report=report,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.APPROVED,
    )

    ReportPublishRequestFactory.create_batch(5)

    request = rf.get("?state=approved")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report.pk}


def test_reportlist_filter_by_state_pending(rf, core_developer):
    report = ReportFactory()
    ReportPublishRequestFactory(report=report)

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

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report.pk}


def test_reportlist_filter_by_state_rejected(rf, core_developer):
    report = ReportFactory()
    ReportPublishRequestFactory(
        report=report,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.REJECTED,
    )

    ReportPublishRequestFactory.create_batch(5)

    request = rf.get("?state=rejected")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report.pk}


def test_reportlist_filter_by_org(rf, core_developer):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    rfile = ReleaseFileFactory(workspace=workspace)

    r1 = ReportFactory(release_file=rfile)
    ReportFactory.create_batch(2)

    request = rf.get(f"/?org={org.slug}")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {r1.pk}


def test_reportlist_filter_by_project(rf, core_developer):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)
    rfile = ReleaseFileFactory(workspace=workspace)

    r1 = ReportFactory(release_file=rfile)
    ReportFactory.create_batch(2)

    request = rf.get(f"/?project={project.slug}")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {r1.pk}


def test_reportlist_filter_by_user(rf, core_developer):
    user = UserFactory()

    r1 = ReportFactory(created_by=user)
    ReportFactory.create_batch(2)

    request = rf.get(f"/?user={user.username}")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {r1.pk}


def test_reportlist_search(rf, core_developer):
    user = UserFactory(username="beng")

    r1 = ReportFactory(created_by=user)
    ReportFactory.create_batch(2)

    request = rf.get("/?q=ben")
    request.user = core_developer
    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {r1.pk}


def test_reportlist_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ReportList.as_view()(request)


def test_reportpublishrequestapprove_success(rf, core_developer, mailoutbox):
    publish_request = ReportPublishRequestFactory(decision_at=None)

    request = rf.post("/")
    request.user = core_developer

    response = ReportPublishRequestApprove.as_view()(
        request,
        pk=publish_request.report.pk,
        publish_request_pk=publish_request.pk,
    )

    assert response.status_code == 302
    assert response.url == publish_request.report.get_staff_url()

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
        ReportPublishRequestApprove.as_view()(
            request,
            pk=publish_request.report.pk,
            publish_request_pk=publish_request.pk,
        )


def test_reportpublishrequestapprove_unknown_publish_request(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ReportPublishRequestApprove.as_view()(request, pk="0", publish_request_pk="0")


def test_reportpublishrequestreject_success(rf, core_developer):
    publish_request = ReportPublishRequestFactory(decision_at=None)

    request = rf.post("/")
    request.user = core_developer

    response = ReportPublishRequestReject.as_view()(
        request, pk=publish_request.report.pk, publish_request_pk=publish_request.pk
    )

    assert response.status_code == 302
    assert response.url == publish_request.report.get_staff_url()

    publish_request.refresh_from_db()
    assert publish_request.decision_at
    assert publish_request.decision_by == core_developer
    assert publish_request.decision == ReportPublishRequest.Decisions.REJECTED


def test_reportpublishrequestreject_unauthorized(rf):
    publish_request = ReportPublishRequestFactory()

    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        ReportPublishRequestReject.as_view()(
            request,
            pk=publish_request.report.pk,
            publish_request_pk=publish_request.pk,
        )


def test_reportpublishrequestreject_unknown_publish_request(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ReportPublishRequestReject.as_view()(request, pk="0", publish_request_pk="0")
