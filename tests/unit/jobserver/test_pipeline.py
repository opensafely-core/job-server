from jobserver.pipeline import notify_on_new_user, set_notifications_email

from ...factories import UserFactory


def test_notify_on_new_user_with_existing_user(slack_messages):
    user = UserFactory()
    notify_on_new_user(user, is_new=False)
    assert len(slack_messages) == 0


def test_notify_on_new_user_with_new_user(slack_messages):
    user = UserFactory()

    notify_on_new_user(user, is_new=True)

    url = f"http://localhost:8000{user.get_staff_url()}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "job-server-registrations"
    assert text == f"New user ({user.username}) registered: <{url}>"


def test_set_notifications_email_already_set():
    user = UserFactory(
        email="test@example.com", notifications_email="notifications@example.com"
    )

    set_notifications_email(user=user)

    user.refresh_from_db()
    assert user.notifications_email == "notifications@example.com"


def test_set_notifications_email_new_user():
    user = UserFactory(email="test@example.com", notifications_email="")

    set_notifications_email(user=user)

    user.refresh_from_db()
    assert user.notifications_email == "test@example.com"
