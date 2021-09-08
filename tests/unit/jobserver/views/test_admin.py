from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse

from jobserver.models import Backend
from jobserver.views.admin import ApproveUsers

from ....factories import OrgFactory, UserFactory


def test_approveusers_as_non_superuser(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = ApproveUsers.as_view()(request)

    assert response.status_code == 302
    assert response.url == "/login/github/?next=/"


def test_approveusers_get_success(rf):
    user = UserFactory(is_superuser=True)
    request = rf.get(f"/?user={user.pk}")
    request.user = user

    response = ApproveUsers.as_view()(request)

    assert response.status_code == 200

    assert list(response.context_data["users"]) == [user]


def test_approveusers_post_success(rf):
    user1 = UserFactory()
    user2 = UserFactory()

    org1 = OrgFactory()

    # create a second Org to check assignment is only being done for the
    # selected orgs
    OrgFactory()

    test = Backend.objects.get(slug="test")
    tpp = Backend.objects.get(slug="tpp")

    data = {
        "backends": [test.pk, tpp.pk],
        "orgs": [org1.pk],
    }
    request = rf.post(f"/?user={user1.pk}&user={user2.pk}", data)
    request.user = UserFactory(is_superuser=True)

    # set up messages framework
    request.session = "session"
    request._messages = FallbackStorage(request)

    response = ApproveUsers.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("admin:jobserver_user_changelist")

    user1.refresh_from_db()
    assert set(user1.backends.all()) == {test, tpp}
    assert list(user1.orgs.all()) == [org1]

    user2.refresh_from_db()
    assert set(user2.backends.all()) == {test, tpp}
    assert list(user2.orgs.all()) == [org1]


def test_approveusers_with_invalid_form(rf):
    user = UserFactory(is_superuser=True)

    request = rf.post(f"/?user={user.pk}")
    request.user = user

    response = ApproveUsers.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["form"].errors


def test_approveusers_with_no_users(rf):
    user = UserFactory(is_superuser=True)

    request = rf.get("/")
    request.user = user

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApproveUsers.as_view()(request)

    assert response.status_code == 302
    assert response.url == reverse("admin:jobserver_user_changelist")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "One or more users must be selected"
