from jobserver.pipeline import notify_on_new_user, set_notifications_email

from ...factories import UserFactory


def test_notify_on_new_user_with_existing_user(mocker):
    user = UserFactory()

    mock = mocker.patch("jobserver.pipeline.slack_client", autospec=True)

    notify_on_new_user(user, is_new=False)

    mock.chat_postMessage.assert_not_called()


def test_notify_on_new_user_with_new_user(mocker):
    user = UserFactory()

    mock = mocker.patch("jobserver.pipeline.slack_client", autospec=True)

    notify_on_new_user(user, is_new=True)

    mock.chat_postMessage.assert_called_once()

    url = f"http://localhost:8000{user.get_staff_url()}"
    mock.chat_postMessage.assert_called_with(
        channel="job-server-registrations",
        text=f"New user ({user.username}) registered: {url}",
    )


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
