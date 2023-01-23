from ....factories import OrgFactory, OrgMembershipFactory, UserFactory


def test_orgmembership_str():
    org = OrgFactory(name="EBMDataLab")
    user = UserFactory(username="ben")

    membership = OrgMembershipFactory(org=org, user=user)

    assert str(membership) == "ben | EBMDataLab"
