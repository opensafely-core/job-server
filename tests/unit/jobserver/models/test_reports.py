import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Report, ReportPublishRequest
from jobserver.utils import set_from_qs

from ....factories import (
    AnalysisRequestFactory,
    ReportFactory,
    ReportPublishRequestFactory,
    UserFactory,
)


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_report_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReportFactory(**{field: None})


def test_report_get_staff_url():
    report = ReportFactory()

    url = report.get_staff_url()

    assert url == reverse("staff:report-detail", kwargs={"pk": report.pk})


def test_report_str():
    report = ReportFactory(title="test")

    assert str(report) == "test"


def test_report_published_check_constraint_missing_at():
    with pytest.raises(IntegrityError):
        ReportFactory(published_at=None, published_by=UserFactory())


def test_report_published_check_constraint_missing_by():
    with pytest.raises(IntegrityError):
        # published_at uses auto_now so any value we passed in here is ignored
        ReportFactory(published_at=timezone.now(), published_by=None)


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
    request = ReportPublishRequestFactory()
    user = UserFactory()

    request.approve(user=user)

    request.refresh_from_db()
    assert request.approved_at == timezone.now()
    assert request.approved_by == user

    assert request.report.published_at == timezone.now()
    assert request.report.published_by == user

    rfile_publish_request = request.release_file_publish_request

    snapshot_files = rfile_publish_request.snapshot.files.all()
    assert set_from_qs(snapshot_files) == set_from_qs(rfile_publish_request.files.all())
    assert rfile_publish_request.snapshot.created_by == user
    assert rfile_publish_request.snapshot.published_at == timezone.now()
    assert rfile_publish_request.snapshot.published_by == user

    assert rfile_publish_request.approved_at == timezone.now()
    assert rfile_publish_request.approved_by == user


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

    # have we constructed a ReleaseFilePublishRequest correctly?
    assert request.release_file_publish_request.created_by == user
    assert set_from_qs(request.release_file_publish_request.files.all()) == {
        report.release_file.pk
    }
    assert (
        request.release_file_publish_request.workspace == report.release_file.workspace
    )


def test_reportpublishrequest_get_absolute_url():
    report = ReportFactory(title="Testing Report")
    publish_request = ReportPublishRequestFactory(report=report)

    url = publish_request.get_absolute_url()

    assert url == reverse(
        "interactive:report-publish-request-update",
        kwargs={
            "org_slug": report.project.org.slug,
            "project_slug": report.project.slug,
            "slug": report.slug,
            "pk": publish_request.pk,
        },
    )


def test_reportpublishrequest_str():
    report = ReportFactory(title="Testing Report")
    publish_request = ReportPublishRequestFactory(report=report)
    assert str(publish_request) == "Publish request for report: Testing Report"
