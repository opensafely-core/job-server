import pytest
from django.db import IntegrityError
from django.urls import reverse

from interactive.models import AnalysisRequest

from ...factories import (
    AnalysisRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    ReportPublishRequestFactory,
    UserFactory,
)


def test_analysisrequest_constraints_updated_at_and_updated_by_both_set():
    AnalysisRequestFactory(updated_by=UserFactory())


@pytest.mark.django_db(transaction=True)
def test_analysisrequest_constraints_missing_updated_at_or_updated_by():
    with pytest.raises(IntegrityError):
        AnalysisRequestFactory(updated_by=None)

    with pytest.raises(IntegrityError):
        ar = AnalysisRequestFactory(updated_by=UserFactory())

        # use update to work around auto_now always firing on save()
        AnalysisRequest.objects.filter(pk=ar.pk).update(updated_at=None)


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_analysisrequest_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        AnalysisRequestFactory(**{field: None})


def test_analysisrequest_get_absolute_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_absolute_url()

    assert url == reverse(
        "interactive:analysis-detail",
        kwargs={
            "org_slug": analysis_request.project.org.slug,
            "project_slug": analysis_request.project.slug,
            "slug": analysis_request.slug,
        },
    )


def test_analysisrequest_get_publish_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_publish_url()

    assert url == reverse(
        "interactive:report-publish-request-create",
        kwargs={
            "org_slug": analysis_request.project.org.slug,
            "project_slug": analysis_request.project.slug,
            "slug": analysis_request.slug,
        },
    )


def test_analysisrequest_get_staff_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_staff_url()

    assert url == reverse(
        "staff:analysis-request-detail", kwargs={"slug": analysis_request.slug}
    )


def test_analysisrequest_get_edit_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_edit_url()

    assert url == reverse(
        "interactive:report-edit",
        kwargs={
            "org_slug": analysis_request.project.org.slug,
            "project_slug": analysis_request.project.slug,
            "slug": analysis_request.slug,
        },
    )


def test_analysisrequest_publish_success():
    report = ReportFactory()
    publish_request = ReportPublishRequestFactory(report=report)
    analysis_request = AnalysisRequestFactory(report=report)

    assert analysis_request.publish_request == publish_request


def test_analysisrequest_publish_without_report():
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.publish_request is None


def test_analysisrequest_publish_without_report_publish_request():
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    assert analysis_request.publish_request is None


def test_analysisrequest_str():
    analysis_request = AnalysisRequestFactory()

    assert str(analysis_request) == analysis_request.title


def test_analysisrequest_visible_to_creator():
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(analysis_request.created_by)


def test_analysisrequest_visible_to_staff(core_developer):
    analysis_request = AnalysisRequestFactory()

    assert analysis_request.visible_to(core_developer)


def test_analysisrequest_visible_to_other_user():
    analysis_request = AnalysisRequestFactory()

    assert not analysis_request.visible_to(UserFactory())


def test_analysisrequest_report_content_success():
    rfile = ReleaseFileFactory()
    rfile.absolute_path().write_text("testing")
    report = ReportFactory(release_file=rfile)
    analysis_request = AnalysisRequestFactory(report=report)

    assert analysis_request.report_content == "testing"


def test_analysisrequest_report_content_with_no_release_file():
    rfile = ReleaseFileFactory()
    report = ReportFactory(release_file=rfile)
    analysis_request = AnalysisRequestFactory(report=report)

    assert analysis_request.report_content == ""


def test_analysisrequest_report_content_with_no_report():
    assert AnalysisRequestFactory().report_content == ""


def test_analysisrequest_ulid():
    assert AnalysisRequestFactory().ulid.timestamp
