from jobserver.authorization import CoreDeveloper, ProjectCollaborator
from jobserver.authorization.mappers import get_project_roles_for_user

from ....factories import (
    ProjectFactory,
    UserFactory,
)


def test_get_project_roles_for_user_with_roles(project_membership):
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    project_membership(project=project, user=user, roles=[ProjectCollaborator])

    roles = get_project_roles_for_user(project, user)

    assert roles == [ProjectCollaborator]


def test_get_project_roles_for_user_unknown_membership():
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    assert get_project_roles_for_user(project, user) == []


def test_get_project_roles_for_user_without_roles(project_membership):
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    project_membership(project=project, user=user, roles=[])
    roles = get_project_roles_for_user(project, user)

    assert roles == []
