from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from jobserver.authorization import InteractiveReporter
from jobserver.views.users import ResetPassword, Settings, login_view

from ....factories import (
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    UserSocialAuthFactory,
)


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


def test_setpassword_with_interactive_role(client):
    project = ProjectFactory()
    user = UserFactory(fullname="test", password="test", roles=[InteractiveReporter])
    ProjectMembershipFactory(project=project, user=user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = client.get(user.get_password_reset_url(), follow=True)
    assert response.status_code == 200
    reset_url = f"/reset-password/{uid}/set-password/"
    assert response.redirect_chain == [(reset_url, 302)]

    # don't follow the redirect here because it goes to AnalysisRequestCreate
    # which wants to hit the network to look up codelists on OpenCodelists.
    # Switching to a RequestFactory for this assertion also isn't ideal because
    # Django's PasswordResetConfirmView (which SetPassword subclasses) performs
    # a redirect to avoid exposing the reset token in the URL (saving it to the
    # session), and testing that would involve testing a lot of Django's code,
    # which they have already tested, when we only care that the final redirect
    # is performed correctly.
    data = {"new_password1": "testtest1234", "new_password2": "testtest1234"}
    response = client.post(reset_url, data, follow=False)
    assert response.status_code == 302
    assert response.url == project.get_interactive_url()


def test_setpassword_without_interactive_role(rf, client):
    project = ProjectFactory()
    user = UserFactory(fullname="test", password="test")
    ProjectMembershipFactory(project=project, user=user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = client.get(user.get_password_reset_url(), follow=True)
    assert response.status_code == 200
    reset_url = f"/reset-password/{uid}/set-password/"
    assert response.redirect_chain == [(reset_url, 302)]

    data = {"new_password1": "testtest1234", "new_password2": "testtest1234"}
    response = client.post(reset_url, data, follow=True)
    assert response.status_code == 200
    reset_url = f"/reset-password/{uid}/set-password/"
    assert response.redirect_chain == [("/", 302)]


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
