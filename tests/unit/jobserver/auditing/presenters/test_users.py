from jobserver.auditing.presenters import users
from tests.factories import AuditableEventFactory, UserFactory


def test_created_with_known_objects():
    actor = UserFactory()
    target = UserFactory()

    event = AuditableEventFactory(
        created_by=actor.username,
        target_id=target.pk,
        target_user=target.username,
        old="jobserver.authorization.roles.Role1",
        new="jobserver.authorization.roles.Role2,jobserver.authorization.roles.Role3",
    )

    presenter = users.updated_roles(event=event)

    assert presenter.context["actor"].display_value == actor.fullname
    assert presenter.context["actor"].link == actor.get_staff_url()

    assert presenter.context["created_at"] == event.created_at

    assert presenter.context["user"].display_value == target.fullname
    assert presenter.context["user"].link == target.get_staff_url()

    assert presenter.context["before"] == "Role1"
    assert presenter.context["after"] == "Role2, Role3"

    assert presenter.template_name == "staff/auditable_events/user_updated_roles.html"


def test_created_with_unknown_objects():
    event = AuditableEventFactory(
        created_by="User 1",
        target_id="",
        target_user="User 2",
        old="jobserver.authorization.roles.Role1",
        new="jobserver.authorization.roles.Role2,jobserver.authorization.roles.Role3",
    )

    presenter = users.updated_roles(event=event)

    assert presenter.context["actor"].display_value == "User 1"
    assert presenter.context["actor"].link is None

    assert presenter.context["created_at"] == event.created_at

    assert presenter.context["user"].display_value == "User 2"
    assert presenter.context["user"].link is None

    assert presenter.context["before"] == "Role1"
    assert presenter.context["after"] == "Role2, Role3"

    assert presenter.template_name == "staff/auditable_events/user_updated_roles.html"
