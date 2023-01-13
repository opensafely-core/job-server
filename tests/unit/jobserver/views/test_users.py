from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage

from jobserver.views.users import ResetPassword, Settings, login_view

from ....factories import UserFactory, UserSocialAuthFactory


def test_login_empty_next(rf):
    request = rf.get("/?next=")
    request.user = UserFactory()

    response = login_view(request)

    assert response.status_code == 302
    assert response.url == "/"


def test_login_no_path(rf):
    request = rf.get("/")
    request.user = AnonymousUser()
    response = login_view(request)

    assert response.status_code == 200


def test_login_safe_path(rf):
    request = rf.get("/?next=/")
    request.user = AnonymousUser()
    response = login_view(request)

    assert response.status_code == 200


def test_login_unsafe_path(rf):
    request = rf.get("/?next=https://steal-your-bank-details.com/")
    request.user = AnonymousUser()

    response = login_view(request)

    assert response.status_code == 200
    assert response.context_data["next_url"] == ""


def test_login_already_logged_with_next_url(rf):
    request = rf.get("/?next=/next-url/")
    request.user = UserFactory()

    response = login_view(request)

    assert response.status_code == 302
    assert response.url == "/next-url/"


def test_login_already_logged_with_no_next_url(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = login_view(request)

    assert response.status_code == 302
    assert response.url == "/"


def test_resetpassword_get_success(rf):
    request = rf.get("/")

    response = ResetPassword.as_view()(request)

    assert response.status_code == 200


def test_resetpassword_post_email_only_user(rf, mailoutbox):
    user = UserFactory()

    request = rf.post("/", {"email": user.email})

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ResetPassword.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == "/"

    assert len(mailoutbox) == 1
    assert "reset-password" in mailoutbox[0].body

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Your password reset request was successfully sent."


def test_resetpassword_post_github_user(rf, mailoutbox):
    user = UserSocialAuthFactory().user

    request = rf.post("/", {"email": user.email})

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ResetPassword.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == "/"

    assert len(mailoutbox) == 1
    assert "github" in mailoutbox[0].body

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Your password reset request was successfully sent."


def test_resetpassword_post_unknown_user(rf, mailoutbox):
    request = rf.post("/", {"email": "test@example.com"})

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ResetPassword.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == "/"

    assert len(mailoutbox) == 0

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Your password reset request was successfully sent."


def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get("/")
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert response.context_data["object"] == user2


def test_settings_post(rf):
    UserFactory()
    user2 = UserFactory(
        fullname="Ben Goldacre",
        notifications_email="original@example.com",
    )

    data = {
        "fullname": "Mr Testerson",
        "notifications_email": "changed@example.com",
    }
    request = rf.post("/", data)
    request.user = user2

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = Settings.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"

    user2.refresh_from_db()

    assert user2.notifications_email == "changed@example.com"
    assert user2.fullname == "Mr Testerson"

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"
