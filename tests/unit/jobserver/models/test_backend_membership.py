from ....factories import BackendFactory, BackendMembershipFactory, UserFactory


def test_backendmembership_str():
    backend = BackendFactory(name="Test Backend")
    user = UserFactory(username="ben")

    membership = BackendMembershipFactory(backend=backend, user=user)

    assert str(membership) == "ben | Test Backend"
