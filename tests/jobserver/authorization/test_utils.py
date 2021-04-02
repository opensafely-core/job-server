import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.authorization import (
    OutputPublisher,
    ProjectCollaborator,
    ProjectCoordinator,
    has_permission,
    has_role,
)

from ...factories import ProjectFactory, ProjectMembershipFactory, UserFactory


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
    user = UserFactory(roles=[OutputPublisher])

    assert not has_role(user, ProjectCoordinator)


@pytest.mark.django_db
def test_has_roles_success():
    user = UserFactory(roles=[OutputPublisher])

    assert has_role(user, OutputPublisher)


@pytest.mark.django_db
def test_has_role_unauthenticated():
    user = AnonymousUser()

    assert not has_role(user, ProjectCoordinator)


@pytest.mark.django_db
def test_has_role_with_context_failure():
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCollaborator])

    # key must be a known key
    with pytest.raises(
        ValueError, match="Some invalid keys were used in the context:\n - test"
    ):
        has_role(user, ProjectCollaborator, test=project)

    # value must be the correct type
    with pytest.raises(
        ValueError, match='key "project" got a User, expected a Project'
    ):
        has_role(user, ProjectCollaborator, project=user)


@pytest.mark.django_db
def test_has_role_with_context_success():
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCollaborator])
    assert has_role(user, ProjectCollaborator, project=project)
