import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.authorization import has_permission, has_role

from ...factories import UserFactory


class RoleA:
    permissions = ["perm1", "perm2"]


class RoleB:
    permissions = ["perm3", "perm4"]


@pytest.mark.django_db
def test_has_permission_failure():
    user = UserFactory(roles=[RoleB])

    assert not has_permission(user, "perm1")


@pytest.mark.django_db
def test_has_permission_success():
    user = UserFactory(roles=[RoleA])

    assert has_permission(user, "perm1")


@pytest.mark.django_db
def test_has_permission_unauthenticated():
    user = AnonymousUser()

    assert not has_permission(user, "perm1")


@pytest.mark.django_db
def test_has_roles_failure():
    user = UserFactory(roles=[RoleB])

    assert not has_role(user, RoleA)


@pytest.mark.django_db
def test_has_roles_success():
    user = UserFactory(roles=[RoleA])

    assert has_role(user, RoleA)


@pytest.mark.django_db
def test_has_role_unauthenticated():
    user = AnonymousUser()

    assert not has_role(user, RoleA)
