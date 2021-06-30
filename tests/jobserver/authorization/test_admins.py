import pytest

from jobserver.authorization.admins import ensure_admins, get_admins
from jobserver.authorization.roles import CoreDeveloper
from jobserver.models import User

from ...factories import UserFactory


@pytest.mark.django_db
def test_ensure_admins_remove_user():
    # is CoreDeveloper now, and will be afterwards
    UserFactory(username="aaa", roles=[CoreDeveloper])

    # is CoreDeveloper now, and won't be afterwards
    UserFactory(username="bbb", roles=[CoreDeveloper])

    # isn't CoreDeveloper now, and will be afterwards
    UserFactory(username="ccc")

    # isn't CoreDeveloper now, and won't be afterwards
    UserFactory(username="ddd")

    ensure_admins(["aaa", "ccc"])

    assert CoreDeveloper in User.objects.get(username="aaa").roles
    assert CoreDeveloper not in User.objects.get(username="bbb").roles
    assert CoreDeveloper in User.objects.get(username="ccc").roles
    assert CoreDeveloper not in User.objects.get(username="ddd").roles


@pytest.mark.django_db
def test_ensure_admins_success():
    user = UserFactory(username="ghickman")
    assert CoreDeveloper not in user.roles

    ensure_admins(["ghickman"])

    user.refresh_from_db()
    assert CoreDeveloper in user.roles


@pytest.mark.django_db
def test_ensure_admins_unknown_user():
    user = UserFactory(username="ghickman")
    assert CoreDeveloper not in user.roles

    with pytest.raises(Exception, match="Unknown admin usernames: test"):
        ensure_admins(["ghickman", "test"])


@pytest.mark.django_db
def test_ensure_admins_unknown_users():
    user = UserFactory(username="ghickman")
    assert CoreDeveloper not in user.roles

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
