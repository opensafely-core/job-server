from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

import jobserver.models.core
from jobserver.authorization import InteractiveReporter
from jobserver.views.users import (
    GenerateLoginToken,
    Login,
    LoginWithToken,
    LoginWithURL,
    Settings,
)

from ....factories import (
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


def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get("/")
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert response.context_data["object"] == user2


def test_settings_post(rf_messages):
    UserFactory()
    user2 = UserFactory(
        fullname="Ben Goldacre",
        notifications_email="original@example.com",
    )

    data = {
        "fullname": "Mr Testerson",
        "notifications_email": "changed@example.com",
    }
    request = rf_messages.post("/", data)
    request.user = user2

    response = Settings.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"

    user2.refresh_from_db()
    assert user2.notifications_email == "changed@example.com"
    assert user2.fullname == "Mr Testerson"

    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"


def test_loginwittoken_success_username(rf_messages):
    user = UserFactory()
    UserSocialAuthFactory(user=user)
    token = user.generate_login_token()

    data = {"user": user.username, "token": token}
    request = rf_messages.post("/login-with-token", data)
    response = LoginWithToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "You have been logged in using a single use token. That token is now invalid."
    )


def test_loginwittoken_success_email(rf_messages):
    user = UserFactory()
    UserSocialAuthFactory(user=user)
    token = user.generate_login_token()

    data = {"user": user.email, "token": token}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "You have been logged in using a single use token. That token is now invalid."
    )


def test_loginwittoken_success_notification_email(rf_messages):
    user = UserFactory()
    user.notifications_email = "foo@bar.com"
    user.save()
    UserSocialAuthFactory(user=user)
    token = user.generate_login_token()

    data = {"user": user.notifications_email, "token": token}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "You have been logged in using a single use token. That token is now invalid."
    )


def test_loginwittoken_invalid_form(rf_messages):
    request = rf_messages.post("/login-with-token", {})

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_no_user(rf_messages):

    data = {"user": "doesnotexist", "token": "token"}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_no_social(rf_messages):
    user = UserFactory()
    token = user.generate_login_token()

    data = {"user": user.email, "token": token}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_bad_token(rf_messages):
    user = UserFactory()
    UserSocialAuthFactory(user=user)

    data = {"user": user.email, "token": "no token"}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_loginwittoken_expired_token(rf_messages):
    user = UserFactory()
    UserSocialAuthFactory(user=user)
    token = user.generate_login_token()
    user.login_token_expires_at = timezone.now() - timedelta(minutes=1)
    user.save()

    data = {"user": user.email, "token": token}
    request = rf_messages.post("/login-with-token", data)

    response = LoginWithToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "login.html"
    messages = list(request._messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Login failed. The user or token may be incorrect, or the token may have expired."
    )


def test_generate_login_token_login_required(rf):
    request = rf.get("/generate-login-token")
    request.user = AnonymousUser()
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/login/?next=/generate-login-token"

    request = rf.post("/generate-login-token")
    request.user = AnonymousUser()
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/login/?next=/generate-login-token"


def test_generate_login_token_get_success(rf):
    user = UserFactory()
    UserSocialAuthFactory(user=user)
    request = rf.get("/generate-login-token")
    request.user = user
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "generate-login-token.html"
    assert (
        "For logging in to OpenSAFELY from secure Level 4 environments"
        in response.rendered_content
    )


def test_generate_login_token_get_not_social(rf):
    user = UserFactory()
    request = rf.get("/generate-login-token")
    request.user = user
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "generate-login-token.html"
    assert (
        "Only OpenSAFELY users with a linked Github account"
        in response.rendered_content
    )


def test_generate_login_token_post_success(rf, monkeypatch):
    monkeypatch.setattr(
        jobserver.models.core, "human_memorable_token", lambda: "12345678"
    )

    user = UserFactory()
    UserSocialAuthFactory(user=user)
    request = rf.post("/generate-login-token")
    request.user = user
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "generate-login-token.html"
    assert "1234 5678" in response.rendered_content

    user.validate_login_token("1234 5678")


def test_generate_login_token_post_no_social(rf, monkeypatch):
    monkeypatch.setattr(
        jobserver.models.core,
        "human_memorable_token",
        lambda: "12345678",  # pragma: no cover
    )

    user = UserFactory()
    request = rf.post("/generate-login-token")
    request.user = user
    response = GenerateLoginToken.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "generate-login-token.html"
    assert "1234 5678" not in response.rendered_content
