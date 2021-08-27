import pytest

from jobserver.authorization import CoreDeveloper, OrgCoordinator, ProjectCoordinator
from jobserver.authorization.mappers import (
    get_org_roles_for_user,
    get_project_roles_for_user,
)

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_get_org_roles_for_user_with_roles():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])

    roles = get_org_roles_for_user(org, user)

    assert roles == [OrgCoordinator]


@pytest.mark.django_db
def test_get_org_roles_for_user_unknown_membership():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    assert get_org_roles_for_user(org, user) == []


@pytest.mark.django_db
def test_get_org_roles_for_user_without_roles():
    org = OrgFactory()
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user)

    roles = get_org_roles_for_user(org, user)

    assert roles == []


@pytest.mark.django_db
def test_get_project_roles_for_user_with_roles():
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCoordinator])

    roles = get_project_roles_for_user(project, user)

    assert roles == [ProjectCoordinator]


@pytest.mark.django_db
def test_get_project_roles_for_user_unknown_membership():
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    assert get_project_roles_for_user(project, user) == []


@pytest.mark.django_db
def test_get_project_roles_for_user_without_roles():
    project = ProjectFactory()
    user = UserFactory(roles=[CoreDeveloper])

    ProjectMembershipFactory(project=project, user=user, roles=[])
    roles = get_project_roles_for_user(project, user)

    assert roles == []
