from jobserver.pipeline import set_notifications_email

from ...factories import UserFactory


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
