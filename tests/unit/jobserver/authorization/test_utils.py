import pytest
from django.contrib.auth.models import AnonymousUser

from jobserver.authorization import (
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
    has_permission,
    has_role,
    roles_for,
    roles_with_permission,
    strings_to_roles,
)
from jobserver.models import ProjectMembership

from ....factories import ProjectFactory, UserFactory


def test_has_permission_failure():
    # ensure a stable test since roles must be from our defined roles
    assert OutputPublisher.permissions == ["snapshot_publish"]

    user = UserFactory(roles=[OutputPublisher])

    assert not has_permission(user, "perm1")


def test_has_permission_success():
    # ensure a stable test since roles must be from our defined roles
    assert OutputPublisher.permissions == ["snapshot_publish"]

    user = UserFactory(roles=[OutputPublisher])

    assert has_permission(user, "snapshot_publish")


def test_has_permission_unauthenticated():
    user = AnonymousUser()

    assert not has_permission(user, "perm1")


def test_has_roles_failure():
    user = UserFactory(roles=[OutputPublisher])

    assert not has_role(user, ProjectCollaborator)


def test_has_roles_success():
    user = UserFactory(roles=[OutputPublisher])

    assert has_role(user, OutputPublisher)


def test_has_role_unauthenticated():
    user = AnonymousUser()

    assert not has_role(user, ProjectCollaborator)


def test_has_role_with_context_failure(project_membership):
    project = ProjectFactory()
    user = UserFactory()

    project_membership(project=project, user=user, roles=[ProjectCollaborator])

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


def test_has_role_with_context_success(project_membership):
    project = ProjectFactory()
    user = UserFactory()

    project_membership(project=project, user=user, roles=[ProjectCollaborator])
    assert has_role(user, ProjectCollaborator, project=project)


def test_roles_for_success():
    output = roles_for(ProjectMembership)

    assert output == [ProjectCollaborator, ProjectDeveloper]


def test_strings_to_roles_success():
    roles = strings_to_roles(["ProjectDeveloper"])

    assert len(roles) == 1
    assert roles[0] == ProjectDeveloper


def test_strings_to_roles_with_unknown_roles():
    msg = "Unknown Roles:\n - DummyRole\nAvailable Roles are:.*"
    with pytest.raises(Exception, match=msg):
        strings_to_roles(["DummyRole"])


def test_roles_with_permission(role_factory):
    fake_permission = "foo"
    role_with_permission0 = role_factory(permission=fake_permission)
    role_with_permission1 = role_factory(permission=fake_permission)

    role_with_permission = roles_with_permission(permission=fake_permission)
    assert set(role_with_permission) == {role_with_permission0, role_with_permission1}
