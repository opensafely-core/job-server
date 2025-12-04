from applications.emails import send_submitted_application_email

from ...factories import ApplicationFactory


def test_send_finished_notification(mailoutbox):
    application = ApplicationFactory()
    application.submitted_by = application.created_by

    send_submitted_application_email("test@example.com", application)

    m = mailoutbox[0]

    assert list(m.to) == ["test@example.com"]
    assert m.body_contains(application.get_absolute_url())
    assert m.body_contains(application.submitted_by.fullname)
    assert m.body_contains(f"ref: {application.pk_hash}")
