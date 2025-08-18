import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from jobserver.commands import users
from jobserver.utils import set_from_list
from jobserver.views.users import (
    Login,
    RequireName,
    Settings,
    UserDetail,
    UserEventLog,
    UserList,
)

from ....factories import (
    BackendMembershipFactory,
    JobRequestFactory,
    PartialFactory,
    UserFactory,
    UserSocialAuthFactory,
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


# We used to allow POST to the login page, and now do not.
def test_login_post_unauthorised(rf_messages):
    user = UserFactory()

    request = rf_messages.post("/", {"email": user.email})
    request.user = AnonymousUser()

    response = Login.as_view()(request)

    assert response.status_code == 405


def test_requirename_already_logged_in(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = RequireName.as_view()(request)

    assert response.url == "/"
    assert response.status_code == 302


def test_requirename_success(rf):
    partial = PartialFactory()
    request = rf.get(f"/?partial_token={partial.token}")
    request.user = AnonymousUser()

    response = RequireName.as_view()(request)

    assert response.status_code == 200


def test_requirename_with_no_partial_token(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = RequireName.as_view()(request)

    assert response.url == "/"
    assert response.status_code == 302


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
    assert user2.email in response.rendered_content


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
        email="original@example.com",
    )

    data = {
        "fullname": "Mr Testerson",
        "email": "changed@example.com",
        "settings": "",  # button name
    }
    request = rf_messages.post("/", data)
    request.user = user2

    response = Settings.as_view()(request)

    assert response.status_code == 200

    user2.refresh_from_db()
    assert user2.email == "changed@example.com"
    assert user2.fullname == "Mr Testerson"

    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"


def test_settings_user_post_invalid(rf_messages):
    user = UserFactory(
        fullname="Ben Goldacre",
        email="original@example.com",
    )

    data = {
        "fullname": "",
        "email": "notvalidemail",
        "settings": "",  # button name
    }
    request = rf_messages.post("/", data)
    request.user = user

    response = Settings.as_view()(request)

    assert response.status_code == 200

    user.refresh_from_db()
    assert user.fullname == "Ben Goldacre"
    assert user.email == "original@example.com"

    messages = list(request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Invalid settings"


def test_settings_token_post_success(rf, monkeypatch, token_login_user, mailoutbox):
    monkeypatch.setattr(users, "human_memorable_token", lambda: "foo bar baz")

    request = rf.post("/settings", {"token": ""})  # button name
    request.user = token_login_user
    response = Settings.as_view()(request)

    assert response.status_code == 200
    assert response.template_name == "settings.html"
    # temporarily disable for initial deploy
    assert "foo bar baz" in response.rendered_content

    users.validate_login_token(token_login_user.username, "foo bar baz")

    assert "new login token" in mailoutbox[0].body


def test_settings_token_post_invalid_user(rf_messages, monkeypatch):
    # this shouldn't be used, but set it anyway so we can detect if it is used
    monkeypatch.setattr(
        users,
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


def test_userdetail_success(rf):
    user = UserFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetail_num_queries(rf, django_assert_num_queries):
    user = UserFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(1):
        response = UserDetail.as_view()(request, username=user.username)
        assert response.status_code == 200

    with django_assert_num_queries(4):
        response.render()


def test_userdetail_unknown_user(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        UserDetail.as_view()(request, username="")


def test_usereventlog_success(rf):
    user = UserFactory()

    job_requests = JobRequestFactory.create_batch(5, created_by=user)

    request = rf.get("/")
    request.user = user

    response = UserEventLog.as_view()(request, username=user.username)

    assert response.status_code == 200

    expected = set_from_list(job_requests)
    assert set_from_list(response.context_data["object_list"]) == expected


def test_usereventlog_num_queries(rf, django_assert_num_queries):
    user = UserFactory()

    JobRequestFactory.create_batch(5, created_by=user)

    request = rf.get("/")
    request.user = user

    with django_assert_num_queries(2):
        response = UserEventLog.as_view()(request, username=user.username)
        assert response.status_code == 200

    with django_assert_num_queries(11):
        response.render()


def test_usereventlog_unknown_user(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        UserEventLog.as_view()(request, username="")


def test_userlist_success(rf):
    users = UserFactory.create_batch(5)
    user = UserFactory()

    request = rf.get("/")
    request.user = user

    response = UserList.as_view()(request)

    assert response.status_code == 200

    # account for the user attached to the request
    expected = set_from_list(users + [user])
    assert set_from_list(response.context_data["object_list"]) == expected


def test_userlist_num_queries(rf, django_assert_num_queries):
    UserFactory.create_batch(5)

    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(1):
        response = UserList.as_view()(request)
        assert response.status_code == 200

    with django_assert_num_queries(4):
        response.render()
