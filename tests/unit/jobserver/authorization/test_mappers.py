from jobserver.authorization import CoreDeveloper, OrgCoordinator, ProjectCollaborator
from jobserver.authorization.mappers import (
    get_org_roles_for_user,
    get_project_roles_for_user,
)

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
)


def test_get_org_roles_for_user_with_roles():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])

    roles = get_org_roles_for_user(org, user)

    assert roles == [OrgCoordinator]


def test_get_org_roles_for_user_unknown_membership():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    assert get_org_roles_for_user(org, user) == []


def test_get_org_roles_for_user_without_roles():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user)

    roles = get_org_roles_for_user(org, user)

    assert roles == []


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
