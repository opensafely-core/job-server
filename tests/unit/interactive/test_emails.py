from interactive.emails import send_report_uploaded_notification

from ...factories import AnalysisRequestFactory, ReportFactory


def test_send_report_uploaded_notification(mailoutbox):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    send_report_uploaded_notification(analysis_request)

    m = mailoutbox[0]
    text_content = m.body
    html_content = m.alternatives[0][0]

    assert analysis_request.get_absolute_url() in text_content
    assert analysis_request.get_absolute_url() in html_content
    assert analysis_request.report.title in text_content
    assert analysis_request.report.title in html_content
    assert list(m.to) == [analysis_request.created_by.email]
