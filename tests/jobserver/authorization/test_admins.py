import pytest

from jobserver.authorization.admins import ensure_admins, get_admins
from jobserver.authorization.roles import SuperUser
from jobserver.models import User

from ...factories import UserFactory


@pytest.mark.django_db
def test_ensure_admins_remove_user():
    # is superuser now, and will be afterwards
    UserFactory(username="aaa", roles=[SuperUser])

    # is superuser now, and won't be afterwards
    UserFactory(username="bbb", roles=[SuperUser])

    # isn't superuser now, and will be afterwards
    UserFactory(username="ccc")

    # isn't superuser now, and won't be afterwards
    UserFactory(username="ddd")

    ensure_admins(["aaa", "ccc"])

    assert SuperUser in User.objects.get(username="aaa").roles
    assert SuperUser not in User.objects.get(username="bbb").roles
    assert SuperUser in User.objects.get(username="ccc").roles
    assert SuperUser not in User.objects.get(username="ddd").roles


@pytest.mark.django_db
def test_ensure_admins_success():
    user = UserFactory(username="ghickman")
    assert SuperUser not in user.roles

    ensure_admins(["ghickman"])

    user.refresh_from_db()
    assert SuperUser in user.roles


@pytest.mark.django_db
def test_ensure_admins_unknown_user():
    user = UserFactory(username="ghickman")
    assert SuperUser not in user.roles

    with pytest.raises(Exception, match="Unknown admin usernames: test"):
        ensure_admins(["ghickman", "test"])


@pytest.mark.django_db
def test_ensure_admins_unknown_users():
    user = UserFactory(username="ghickman")
    assert SuperUser not in user.roles

    with pytest.raises(Exception, match="Unknown admin usernames: foo, test"):
        ensure_admins(["ghickman", "foo", "test"])


def test_get_admins_empty(monkeypatch):
    monkeypatch.setenv("ADMIN_USERS", "")
    assert get_admins() == []


def test_get_admins_space_around_comma(monkeypatch):
    monkeypatch.setenv("ADMIN_USERS", "test , foo")
    assert get_admins() == ["test", "foo"]


def test_get_admins_success(monkeypatch):
    monkeypatch.setenv("ADMIN_USERS", "one,two,three")
    assert get_admins() == ["one", "two", "three"]
