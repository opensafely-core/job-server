from applications.emails import send_submitted_application_email

from ...factories import ApplicationFactory


def test_send_finished_notification(mailoutbox):
    application = ApplicationFactory()

    send_submitted_application_email("test@example.com", application)

    m = mailoutbox[0]

    assert application.get_absolute_url() in m.body

    assert list(m.to) == ["test@example.com"]
