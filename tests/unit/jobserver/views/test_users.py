from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from jobserver.authorization import InteractiveReporter
from jobserver.views.users import Login, LoginWithURL, Settings

from ....factories import UserFactory, UserSocialAuthFactory


def test_login_already_logged_in_with_next_url(rf):
    request = rf.get("/?next=/next-url/")
    request.user = UserFactory()

    response = Login.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/next-url/"


def test_login_already_logged_in_with_no_next_url(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = Login.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"


def test_login_get_empty_next(rf):
    request = rf.get("/?next=")
    request.user = UserFactory()

    response = Login.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"


def test_login_get_no_path(rf):
    request = rf.get("/")
    request.user = AnonymousUser()
    response = Login.as_view()(request)

    assert response.status_code == 200


def test_login_get_safe_path(rf):
    request = rf.get("/?next=/")
    request.user = AnonymousUser()
    response = Login.as_view()(request)

    assert response.status_code == 200


def test_login_get_unsafe_path(rf):
    request = rf.get("/?next=https://steal-your-bank-details.com/")
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["next_url"] == ""


def test_login_post_success_with_email_user(rf, mailoutbox):
    user = UserFactory(roles=[InteractiveReporter])

    request = rf.post("/", {"email": user.email})
    request.user = AnonymousUser()

    # set up messages framework
    request.session = SessionStore()
    messages = FallbackStorage(request)
    request._messages = messages

    response = Login.as_view()(request)

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "If you have a user account we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg

    # differentiate from the GitHub user use case
    m = mailoutbox[0]
    assert m.subject == "Log into OpenSAFELY"
    assert "using your GitHub account" not in m.body


def test_login_post_success_with_github_user(rf, mailoutbox):
    user = UserFactory(roles=[InteractiveReporter])
    social = UserSocialAuthFactory(user=user)

    request = rf.post("/", {"email": social.user.email})
    request.user = AnonymousUser()

    # set up messages framework
    request.session = SessionStore()
    messages = FallbackStorage(request)
    request._messages = messages

    response = Login.as_view()(request)

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "If you have a user account we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg

    # differentiate from the email user use case
    m = mailoutbox[0]
    assert m.subject == "Log into OpenSAFELY"
    assert reverse("login") in m.body
    assert "using your GitHub account" in m.body


def test_login_post_unauthorised(rf, mailoutbox):
    user = UserFactory()

    request = rf.post("/", {"email": user.email})
    request.user = AnonymousUser()

    # set up messages framework
    request.session = SessionStore()
    messages = FallbackStorage(request)
    request._messages = messages

    response = Login.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("login")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "Only users who have signed up to OpenSAFELY Interactive can log in via email"
    assert str(messages[0]) == msg


def test_login_post_unknown_user(rf):
    request = rf.post("/", {"email": "test@example.com"})
    request.user = AnonymousUser()

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = Login.as_view()(request)

    assert response.status_code == 200
    assert not response.context_data["form"].errors

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "If you have a user account we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg


def test_loginwithurl_success(rf):
    user = UserFactory(roles=[InteractiveReporter])

    signed_token = TimestampSigner(salt="login").sign("test")

    request = rf.get("/")
    request.session = SessionStore()
    request.session["_login_token"] = user.email

    response = LoginWithURL.as_view()(request, token=signed_token)

    assert response.status_code == 302
    assert response.url == "/"


def test_loginwithurl_unauthorized(rf):
    user = UserFactory()

    signed_token = TimestampSigner(salt="login").sign("test")

    request = rf.get("/")
    request.session = SessionStore()
    request.session["_login_token"] = user.email

    # set up messages framework
    messages = FallbackStorage(request)
    request._messages = messages

    response = LoginWithURL.as_view()(request, token=signed_token)

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "Only users who have signed up to OpenSAFELY Interactive can log in via email"
    assert str(messages[0]) == msg


def test_loginwithurl_unknown_user(rf):
    request = rf.get("/")

    # set up messages framework
    request.session = SessionStore()
    request.session["_login_token"] = "unknown user"
    messages = FallbackStorage(request)
    request._messages = messages

    response = LoginWithURL.as_view()(request, token="")

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_loginwithurl_with_expired_token(rf):
    user = UserFactory()

    new_time = timezone.now() - timedelta(hours=1, seconds=1)
    with freeze_time(new_time):
        signed_pk = TimestampSigner(salt="login").sign(user.pk)
    pk, _, token = signed_pk.partition(":")

    request = rf.get("/")

    # set up messages framework
    request.session = SessionStore()
    messages = FallbackStorage(request)
    request._messages = messages

    response = LoginWithURL.as_view()(request, pk=pk, token=token)

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_loginwithurl_with_invalid_token(rf):
    user = UserFactory()

    request = rf.get("/")

    # set up messages framework
    request.session = SessionStore()
    messages = FallbackStorage(request)
    request._messages = messages

    response = LoginWithURL.as_view()(request, pk=user.pk, token="")

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


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
