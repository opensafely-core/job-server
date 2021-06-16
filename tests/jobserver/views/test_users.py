import pytest
from django.contrib.messages.storage.fallback import FallbackStorage

from jobserver.views.users import Settings, UserList

from ...factories import UserFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_settings_get(rf):
    UserFactory()
    user2 = UserFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = user2
    response = Settings.as_view()(request)

    assert response.status_code == 200

    # check the view was constructed with the request user
    assert response.context_data["object"] == user2


@pytest.mark.django_db
def test_settings_post(rf):
    UserFactory()
    user2 = UserFactory(notifications_email="original@example.com")

    data = {"notifications_email": "changed@example.com"}
    request = rf.post(MEANINGLESS_URL, data)
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


@pytest.mark.django_db
def test_userlist_success(rf, core_developer):
    UserFactory.create_batch(5)

    request = rf.get(MEANINGLESS_URL)
    request.user = core_developer

    response = UserList.as_view()(request)

    assert response.status_code == 200

    # the core_developer fixture creates a User object as well as the 5 we
    # created in the batch call above
    assert len(response.context_data["object_list"]) == 6
