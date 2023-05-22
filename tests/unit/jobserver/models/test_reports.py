import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Report, ReportPublishRequest

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    ReleaseFileFactory,
    ReportFactory,
    ReportPublishRequestFactory,
    SnapshotFactory,
    SnapshotPublishRequestFactory,
    UserFactory,
)


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_report_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReportFactory(**{field: None})


def test_report_get_absolute_url_with_analysis_request():
    project = ProjectFactory()
    report = ReportFactory(project=project)
    AnalysisRequestFactory(project=project, report=report)

    url = report.get_absolute_url()

    assert url == reverse(
        "interactive:analysis-detail",
        kwargs={
            "org_slug": report.project.org.slug,
            "project_slug": report.project.slug,
            "slug": report.analysis_request.slug,
        },
    )


def test_report_get_absolute_url_without_analysis_request():
    report = ReportFactory()

    url = report.get_absolute_url()

    assert url == "/"


def test_report_get_staff_url():
    report = ReportFactory()

    url = report.get_staff_url()

    assert url == reverse("staff:report-detail", kwargs={"pk": report.pk})


def test_report_is_draft():
    report = ReportFactory()
    assert report.is_draft

    publish_request = ReportPublishRequestFactory(report=report)
    assert report.is_draft

    publish_request.approve(user=UserFactory())
    assert not report.is_draft


def test_report_is_locked():
    report = ReportFactory()

    assert not report.is_locked

    ReportPublishRequestFactory(report=report)
    assert report.is_locked

    ReportPublishRequestFactory(
        report=report,
        decision=ReportPublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )
    assert report.is_locked

    ReportPublishRequestFactory(
        report=report,
        decision=ReportPublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )
    assert not report.is_locked


def test_report_is_published():
    report = ReportFactory()
    assert not report.is_published

    publish_request = ReportPublishRequestFactory(report=report)
    assert not report.is_published

    publish_request.approve(user=UserFactory())
    assert report.is_published


def test_report_str():
    report = ReportFactory(title="test")

    assert str(report) == "test"


def test_report_updated_check_constraint_missing_at():
    ReportFactory(updated_by=UserFactory())

    with pytest.raises(IntegrityError):
        # use update here because auto_now doesn't apply to this type of query
        Report.objects.update(updated_at=None)


def test_report_updated_check_constraint_missing_by():
    with pytest.raises(IntegrityError):
        # updated_at uses auto_now so any value we passed in here is ignored
        ReportFactory(updated_by=None)


def test_reportpublishrequest_approve(freezer):
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    snapshot_request = SnapshotPublishRequestFactory(snapshot=snapshot)
    request = ReportPublishRequestFactory(snapshot_publish_request=snapshot_request)
    user = UserFactory()

    request.approve(user=user)

    request.refresh_from_db()
    assert request.decision_at == timezone.now()
    assert request.decision_by == user
    assert request.decision == ReportPublishRequest.Decisions.APPROVED

    assert snapshot_request.decision_at == timezone.now()
    assert snapshot_request.decision_by == user
    assert snapshot_request.decision == ReportPublishRequest.Decisions.APPROVED


def test_reportpublishrequest_create_from_report_without_report():
    request = ReportPublishRequest.create_from_report(report=None, user=UserFactory())

    assert request is None


def test_reportpublishrequest_create_from_report_without_analysis_request():
    report = ReportFactory()
    user = UserFactory()

    with pytest.raises(Exception):
        ReportPublishRequest.create_from_report(report=report, user=user)


def test_reportpublishrequest_create_from_report_success():
    report = ReportFactory()
    AnalysisRequestFactory(report=report)
    user = UserFactory()

    request = ReportPublishRequest.create_from_report(report=report, user=user)

    assert request.created_by == user
    assert request.report == report
    assert request.updated_by == user

    # have we constructed a SnapshotPublishRequest correctly?
    assert request.snapshot_publish_request


def test_reportpublishrequest_get_approve_url():
    publish_request = ReportPublishRequestFactory()

    url = publish_request.get_approve_url()

    assert url == reverse(
        "staff:report-publish-request-approve",
        kwargs={
            "pk": publish_request.report.pk,
            "publish_request_pk": publish_request.pk,
        },
    )


def test_reportpublishrequest_get_reject_url():
    publish_request = ReportPublishRequestFactory()

    url = publish_request.get_reject_url()

    assert url == reverse(
        "staff:report-publish-request-reject",
        kwargs={
            "pk": publish_request.report.pk,
            "publish_request_pk": publish_request.pk,
        },
    )


def test_reportpublishrequest_reject(freezer):
    request = ReportPublishRequestFactory()
    user = UserFactory()

    request.reject(user=user)

    request.refresh_from_db()
    assert request.decision_at == timezone.now()
    assert request.decision_by == user
    assert request.decision == ReportPublishRequest.Decisions.REJECTED


def test_reportpublishrequest_str():
    report = ReportFactory(title="Testing Report")
    publish_request = ReportPublishRequestFactory(report=report)
    assert str(publish_request) == "Publish request for report: Testing Report"
