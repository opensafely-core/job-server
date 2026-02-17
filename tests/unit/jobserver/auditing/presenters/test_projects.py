from jobserver.auditing.presenters import projects
from tests.factories import AuditableEventFactory, ProjectFactory, UserFactory


def test_created_with_known_objects():
    actor = UserFactory()
    project = ProjectFactory()

    event = AuditableEventFactory(
        created_by=actor.username,
        parent_id=project.pk,
    )

    output = projects.created(event=event)

    assert output.context["actor"].display_value == actor.fullname
    assert output.context["actor"].link == actor.get_staff_url()

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == project.name
    assert output.context["project"].link == project.get_staff_url()

    assert output.template_name == "staff/auditable_events/project/created.html"


def test_created_with_unknown_objects():
    event = AuditableEventFactory(created_by="ExampleUser", parent_id="")

    output = projects.created(event=event)

    assert output.context["actor"].display_value == "ExampleUser"
    assert output.context["actor"].link is None

    assert output.context["created_at"] == event.created_at

    assert output.context["project"].display_value == "a Project"
    assert output.context["project"].link is None

    assert output.template_name == "staff/auditable_events/project/created.html"
