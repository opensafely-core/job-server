import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.authorization import (
    OutputPublisher,
    ProjectCoordinator,
    has_permission,
    has_role,
)

from ...factories import UserFactory


@pytest.mark.django_db
def test_has_permission_failure():
    # ensure a stable test since roles must be from our defined roles
    assert OutputPublisher.permissions == ["publish_output"]

    user = UserFactory(roles=[OutputPublisher])

    assert not has_permission(user, "perm1")


@pytest.mark.django_db
def test_has_permission_success():
    # ensure a stable test since roles must be from our defined roles
    assert OutputPublisher.permissions == ["publish_output"]

    user = UserFactory(roles=[OutputPublisher])

    assert has_permission(user, "publish_output")


@pytest.mark.django_db
def test_has_permission_unauthenticated():
    user = AnonymousUser()

    assert not has_permission(user, "perm1")


@pytest.mark.django_db
def test_has_roles_failure():
    user = UserFactory(roles=[ProjectCoordinator])

    assert not has_role(user, OutputPublisher)


@pytest.mark.django_db
def test_has_roles_success():
    user = UserFactory(roles=[ProjectCoordinator])

    assert has_role(user, ProjectCoordinator)


@pytest.mark.django_db
def test_has_role_unauthenticated():
    user = AnonymousUser()

    assert not has_role(user, ProjectCoordinator)
