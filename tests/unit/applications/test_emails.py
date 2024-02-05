from applications.emails import send_submitted_application_email

from ...factories import ApplicationFactory


def test_send_finished_notification(mailoutbox):
    application = ApplicationFactory()
    application.submitted_by = application.created_by

    send_submitted_application_email("test@example.com", application)

    m = mailoutbox[0]
    text_content = m.body
    html_content = m.alternatives[0][0]

    assert list(m.to) == ["test@example.com"]
    assert application.get_absolute_url() in text_content
    assert application.get_absolute_url() in html_content
    assert application.submitted_by.name in text_content
    assert application.submitted_by.name in html_content
    assert f"ref: {application.pk_hash}" in text_content
    assert f"ref: {application.pk_hash}" in html_content
