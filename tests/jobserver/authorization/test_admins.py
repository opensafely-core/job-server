import pytest

from jobserver.authorization.admins import ensure_admins, get_admins
from jobserver.authorization.roles import SuperUser

from ...factories import UserFactory


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
