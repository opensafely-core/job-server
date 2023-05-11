import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import PublishRequest, Report

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    SnapshotFactory,
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

    snapshot = SnapshotFactory()
    snapshot.files.set([report.release_file])
    publish_request = PublishRequestFactory(report=report, snapshot=snapshot)
    assert report.is_draft

    publish_request.approve(user=UserFactory())
    assert not report.is_draft


def test_report_is_locked():
    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile)

    assert not report.is_locked

    PublishRequestFactory(report=report, snapshot=snapshot)
    assert report.is_locked

    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )
    assert report.is_locked

    PublishRequestFactory(
        report=report,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )
    assert not report.is_locked


def test_report_is_published():
    report = ReportFactory()
    assert not report.is_published

    snapshot = SnapshotFactory()
    snapshot.files.set([report.release_file])
    publish_request = PublishRequestFactory(report=report, snapshot=snapshot)
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
