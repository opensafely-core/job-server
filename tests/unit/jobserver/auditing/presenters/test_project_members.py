from jobserver.auditing.presenters import project_members
from tests.factories import (
    AuditableEventFactory,
    ProjectFactory,
    UserFactory,
)


def test_added_with_known_objects():
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    event = AuditableEventFactory(
        created_by=actor.username, target_user=user.username, parent_id=project.pk
    )

    output = project_members.added(event=event)

    assert output.context["actor"].display_value == actor.name
    assert output.context["actor"].link == actor.get_staff_url()

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == project.name
    assert output.context["project"].link == project.get_staff_url()

    assert output.context["user"].display_value == user.name
    assert output.context["user"].link == user.get_staff_url()

    assert output.template_name == "staff/auditable_events/project/members/added.html"


def test_added_with_unknown_objects():
    event = AuditableEventFactory(created_by="beng", target_user="sebbacon")

    output = project_members.added(event=event)

    assert output.context["actor"].display_value == "beng"
    assert output.context["actor"].link is None

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == "a Project"
    assert output.context["project"].link is None

    assert output.context["user"].display_value == "sebbacon"
    assert output.context["user"].link is None

    assert output.template_name == "staff/auditable_events/project/members/added.html"


def test_updated_roles_with_known_objects():
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    event = AuditableEventFactory(
        created_by=actor.username,
        parent_id=project.pk,
        old="jobserver.authorization.roles.ProjectDeveloper",
        new="jobserver.authorization.roles.ProjectCollaborator,jobserver.authorization.roles.ProjectDeveloper",
        target_user=user.username,
    )

    output = project_members.updated_roles(event=event)

    assert output.context["actor"].display_value == actor.name
    assert output.context["actor"].link == actor.get_staff_url()

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == project.name
    assert output.context["project"].link == project.get_staff_url()

    assert output.context["user"].display_value == user.name
    assert output.context["user"].link == user.get_staff_url()

    assert output.context["before"] == "ProjectDeveloper"
    assert output.context["after"] == "ProjectCollaborator, ProjectDeveloper"

    assert (
        output.template_name
        == "staff/auditable_events/project/members/updated_roles.html"
    )


def test_updated_roles_with_unknown_objects():
    event = AuditableEventFactory(
        created_by="beng",
        old="jobserver.authorization.roles.ProjectDeveloper",
        new="jobserver.authorization.roles.ProjectCollaborator,jobserver.authorization.roles.ProjectDeveloper",
    )

    output = project_members.updated_roles(event=event)

    assert output.context["actor"].display_value == "beng"
    assert output.context["actor"].link is None

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == "a Project"
    assert output.context["project"].link is None

    assert output.context["user"].display_value == "Unknown User"
    assert output.context["user"].link is None

    assert output.context["before"] == "ProjectDeveloper"
    assert output.context["after"] == "ProjectCollaborator, ProjectDeveloper"

    assert (
        output.template_name
        == "staff/auditable_events/project/members/updated_roles.html"
    )


def test_removed_with_known_objects():
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    event = AuditableEventFactory(
        created_by=actor.username,
        target_user=user.username,
        parent_id=project.pk,
    )

    output = project_members.removed(event=event)

    assert output.context["actor"].display_value == actor.name
    assert output.context["actor"].link == actor.get_staff_url()

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == project.name
    assert output.context["project"].link == project.get_staff_url()

    assert output.context["user"].display_value == user.name
    assert output.context["user"].link == user.get_staff_url()

    assert output.template_name == "staff/auditable_events/project/members/removed.html"
