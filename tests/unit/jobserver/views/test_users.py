from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

import jobserver.models.core
from jobserver.authorization import InteractiveReporter
from jobserver.views.users import (
    Login,
    LoginWithToken,
    LoginWithURL,
    Settings,
)

from ....factories import (
    BackendFactory,
    BackendMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


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


def test_login_from_backend(rf):
    request = rf.get("/login")
    request.user = AnonymousUser()
    request.backend = BackendFactory()
    response = Login.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["show_token_login"] is True
    assert "Login with Single Use Token" in response.rendered_content
    assert "Sign in with Github" not in response.rendered_content


def test_login_post_success_with_email_user(rf_messages, mailoutbox):
    user = UserFactory(roles=[InteractiveReporter])

    request = rf_messages.post("/", {"email": user.email})
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    msg = "If you have signed up to OpenSAFELY Interactive we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg

    # differentiate from the GitHub user use case
    m = mailoutbox[0]
    assert m.subject == "Log into OpenSAFELY"
    assert "using your GitHub account" not in m.body


def test_login_post_success_with_github_user(rf_messages, mailoutbox):
    user = UserFactory(roles=[InteractiveReporter])
    social = UserSocialAuthFactory(user=user)

    request = rf_messages.post("/", {"email": social.user.email})
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    msg = "If you have signed up to OpenSAFELY Interactive we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg

    # differentiate from the email user use case
    m = mailoutbox[0]
    assert m.subject == "Log into OpenSAFELY"
    assert reverse("login") in m.body
    assert "using your GitHub account" in m.body


def test_login_post_unauthorised(rf_messages, mailoutbox):
    user = UserFactory()

    request = rf_messages.post("/", {"email": user.email})
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    msg = "If you have signed up to OpenSAFELY Interactive we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg


def test_login_post_unknown_user(rf_messages):
    request = rf_messages.post("/", {"email": "test@example.com"})
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 200
    assert not response.context_data["form"].errors

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    msg = "If you have signed up to OpenSAFELY Interactive we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
    assert str(messages[0]) == msg


def test_loginwithurl_bad_token(rf_messages):
    user = UserFactory()

    signed_token = TimestampSigner(salt="login").sign("test")

    request = rf_messages.get("/")
    request.session["_login_token"] = (user.email, "bad token")

    response = LoginWithURL.as_view()(request, token=signed_token)

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_loginwithurl_success(rf):
    project = ProjectFactory()
    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])
    WorkspaceFactory(project=project, name=project.interactive_slug)

    signed_token = TimestampSigner(salt="login").sign("test")

    request = rf.get("/")
    request.session = SessionStore()
    request.session["_login_token"] = (user.email, "test")

    response = LoginWithURL.as_view()(request, token=signed_token)

    assert response.status_code == 302
    assert response.url == project.get_interactive_url()


def test_loginwithurl_unauthorized(rf_messages):
    user = UserFactory()

    signed_token = TimestampSigner(salt="login").sign("test")

    request = rf_messages.get("/")
    request.session = SessionStore()
    request.session["_login_token"] = (user.email, "test")

    response = LoginWithURL.as_view()(request, token=signed_token)

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    msg = "Only users who have signed up to OpenSAFELY Interactive can log in via email"
    assert str(messages[0]) == msg


def test_loginwithurl_unknown_user(rf_messages):
    request = rf_messages.get("/")
    request.session["_login_token"] = ("unknown user", "token")

    response = LoginWithURL.as_view()(request, token="")

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_loginwithurl_with_expired_token(rf_messages):
    user = UserFactory()

    new_time = timezone.now() - timedelta(hours=1, seconds=1)
    with freeze_time(new_time):
        signed_pk = TimestampSigner(salt="login").sign(user.pk)
    pk, _, token = signed_pk.partition(":")

    request = rf_messages.get("/")

    response = LoginWithURL.as_view()(request, pk=pk, token=token)

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_loginwithurl_with_invalid_token(rf_messages):
    user = UserFactory()

    request = rf_messages.get("/")

    response = LoginWithURL.as_view()(request, pk=user.pk, token="")

    assert response.status_code == 302
    assert response.url == "/login/"

    # check we have a message for the user
    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]).startswith("Invalid token, please try again")


def test_settings_login_required(rf):
    request = rf.get("/settings")
    request.user = AnonymousUser()
    response = Settings.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/login/?next=/settings"

    request = rf.post("/settings")
    request.user = AnonymousUser()
    response = Settings.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/login/?next=/settings"


def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get("/")
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert user2.fullname in response.rendered_content
    assert user2.notifications_email in response.rendered_content


def test_settings_get_token_form(rf):
    user = UserFactory()
    request = rf.get("/settings")
    request.user = user

    response = Settings.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "settings.html"
    assert "You can use this to login to OpenSAFELY" not in response.rendered_content

    # add social, but still no backends
    UserSocialAuthFactory(user=user)

    response = Settings.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "settings.html"
    assert "You can use this to login to OpenSAFELY" not in response.rendered_content

    # add backend to user
    BackendMembershipFactory(user=user)

    response = Settings.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "settings.html"
    assert "You can use this to login to OpenSAFELY" in response.rendered_content


def test_settings_user_post(rf_messages):
    UserFactory()
    user2 = UserFactory(
        fullname="Ben Goldacre",
        notifications_email="original@example.com",
    )

    data = {
        "fullname": "Mr Testerson",
        "notifications_email": "changed@example.com",
        "settings": "",  # button name
    }
    request = rf_messages.post("/", data)
    request.user = user2

    response = Settings.as_view()(request)

    assert response.status_code == 200

    user2.refresh_from_db()
    assert user2.notifications_email == "changed@example.com"
    assert user2.fullname == "Mr Testerson"

    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"


def test_settings_user_post_invalid(rf_messages):
    user = UserFactory(
        fullname="Ben Goldacre",
        notifications_email="original@example.com",
    )

    data = {
        "fullname": "",
        "notifications_email": "notvalidemail",
        "settings": "",  # button name
    }
    request = rf_messages.post("/", data)
    request.user = user

    response = Settings.as_view()(request)

    assert response.status_code == 200

    user.refresh_from_db()
    assert user.fullname == "Ben Goldacre"
    assert user.notifications_email == "original@example.com"

    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Invalid settings"


def test_settings_token_post_success(rf, monkeypatch, token_login_user):
    monkeypatch.setattr(
        jobserver.models.core, "human_memorable_token", lambda: "foo bar baz"
    )

    request = rf.post("/settings", {"token": ""})  # button name
    request.user = token_login_user
    response = Settings.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "settings.html"
    # temporarily disable for initial deploy
    assert "foo bar baz" in response.rendered_content

    token_login_user.validate_login_token("foo bar baz")


def test_settings_token_post_invalid_user(rf_messages, monkeypatch):
    # this shouldn't be used, but set it anyway so we can detect if it is used
    monkeypatch.setattr(
        jobserver.models.core,
        "human_memorable_token",
        lambda: "foo bar baz",  # pragma: no cover
    )

    user = UserFactory()
    request = rf_messages.post("/settings", {"token": ""})  # button name
    request.user = user
    response = Settings.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "settings.html"
    assert "foo bar baz" not in response.rendered_content
    messages = list(request._messages)
    assert str(messages[-1]) == "Your account is not allowed to generate a login token"

    # add social, but still no backends
    UserSocialAuthFactory(user=user)

    response = Settings.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "settings.html"
    assert "foo bar baz" not in response.rendered_content
    messages = list(request._messages)
    assert str(messages[-1]) == "Your account is not allowed to generate a login token"


@pytest.mark.parametrize("attr", ["username", "email", "notifications_email"])
def test_loginwittoken_success(attr, rf_messages, token_login_user):
    token = token_login_user.generate_login_token()

    data = {"user": getattr(token_login_user, attr), "token": token}
    request = rf_messages.post("/login-with-token", data)
    request.backend = token_login_user.backends.first()
    response = LoginWithToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "You have been logged in using a single use token. That token is now invalid."
    )


def test_loginwittoken_not_from_backend(rf_messages):
    request = rf_messages.post("/login-with-token", {})
    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert str(messages[-1]) == "Token login only allowed from Level 4"


def test_loginwittoken_no_user(rf_messages):

    data = {"user": "doesnotexist", "token": "token"}
    request = rf_messages.post("/login-with-token", data)
    request.backend = BackendFactory()

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_invalid_user(rf_messages):
    user = UserFactory()
    backend = BackendFactory()

    data = {"user": user.email, "token": "token"}
    request = rf_messages.post("/login-with-token", data)
    request.backend = backend

    response = LoginWithToken.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert (
        str(messages[-1])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )

    UserSocialAuthFactory(user=user)

    response = LoginWithToken.as_view()(request)
    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert (
        str(messages[-1])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_invalid_form(rf_messages, token_login_user):
    request = rf_messages.post("/login-with-token", {})
    request.backend = token_login_user.backends.first()

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_bad_token(rf_messages, token_login_user):
    data = {"user": token_login_user.email, "token": "no token"}
    request = rf_messages.post("/login-with-token", data)
    request.backend = token_login_user.backends.first()

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_expired_token(rf_messages, token_login_user):
    token = token_login_user.generate_login_token()
    token_login_user.login_token_expires_at = timezone.now() - timedelta(minutes=1)
    token_login_user.save()

    data = {"user": token_login_user.email, "token": token}
    request = rf_messages.post("/login-with-token", data)
    request.backend = token_login_user.backends.first()

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )
