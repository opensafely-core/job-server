from interactive.emails import send_report_uploaded_notification, send_welcome_email

from ...factories import AnalysisRequestFactory, ReportFactory, UserFactory


def test_send_report_uploaded_notification(mailoutbox):
    report = ReportFactory()
    analysis_request = AnalysisRequestFactory(report=report)

    send_report_uploaded_notification(analysis_request)

    m = mailoutbox[0]

    assert analysis_request.get_absolute_url() in m.body
    assert analysis_request.report.title in m.body
    assert list(m.to) == [analysis_request.created_by.email]


def test_welcome_email(mailoutbox):
    user = UserFactory()

    send_welcome_email(user)

    m = mailoutbox[0]

    assert user.name in m.body

    assert list(m.to) == [user.email]
