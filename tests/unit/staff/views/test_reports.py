import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from jobserver.models import ReportPublishRequest
from jobserver.utils import set_from_qs
from staff.views.reports import ReportDetail, ReportList

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


def test_reportlist_filter_by_published_requested(rf, core_developer):
    report = ReportFactory()
    ReportPublishRequestFactory(report=report)

    ReportFactory.create_batch(5)

    request = rf.get("?is_published=requested")
    request.user = core_developer

    response = ReportList.as_view()(request)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report.pk}


def test_reportlist_filter_by_published_yes(rf, core_developer):
    report = ReportFactory()
    ReportPublishRequestFactory(
        report=report,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=ReportPublishRequest.Decisions.APPROVED,
    )

    ReportFactory.create_batch(5)

    request = rf.get("?is_published=yes")
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
