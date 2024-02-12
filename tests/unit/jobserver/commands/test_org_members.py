from jobserver.authorization import ProjectDeveloper
from jobserver.commands import org_members as members
from tests.factories import OrgMembershipFactory, UserFactory


def test_update_roles():
    updator = UserFactory()
    membership = OrgMembershipFactory()

    assert membership.roles == []

    members.update_roles(member=membership, by=updator, roles=[ProjectDeveloper])

    membership.refresh_from_db()
    assert membership.roles == [ProjectDeveloper]
