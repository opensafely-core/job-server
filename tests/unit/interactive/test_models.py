from django.urls import reverse

from ...factories import (
    AnalysisRequestFactory,
    ReleaseFileFactory,
    ReportFactory,
    UserFactory,
)


def test_analysisrequest_get_absolute_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_absolute_url()

    assert url == reverse(
        "interactive:analysis-detail",
        kwargs={
            "org_slug": analysis_request.project.org.slug,
            "project_slug": analysis_request.project.slug,
            "pk": analysis_request.pk,
        },
    )


def test_analysisrequest_get_codelist_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_codelist_url()

    assert (
        url
        == f"https://www.opencodelists.org/codelist/{analysis_request.codelist_slug}"
    )


def test_analysisrequest_get_stuff_url():
    analysis_request = AnalysisRequestFactory()

    url = analysis_request.get_staff_url()

    assert url == reverse(
        "staff:analysis-request-detail", kwargs={"pk": analysis_request.pk}
    )


def test_analysisrequest_str():
    analysis_request = AnalysisRequestFactory()

    assert (
        str(analysis_request)
        == f"{analysis_request.title} ({analysis_request.codelist_slug})"
    )


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
