from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage

from jobserver.views.users import Settings, login_view

from ....factories import UserFactory


def test_login_get_no_path(rf):
    request = rf.get("login/")
    request.user = AnonymousUser()
    response = login_view(request)

    assert response.status_code == 200


def test_login_get_safe_path(rf):
    request = rf.get("login/?next=/")
    request.user = AnonymousUser()
    response = login_view(request)

    assert response.status_code == 200


def test_login_get_unsafe_path(rf):
    request = rf.get("login/?next=https://steal-your-bank-details.com/")
    request.user = AnonymousUser()
    response = login_view(request)

    assert response.status_code == 400


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
    user2 = UserFactory(notifications_email="original@example.com")

    data = {"notifications_email": "changed@example.com"}
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

    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Settings saved successfully"
