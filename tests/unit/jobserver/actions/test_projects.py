from jobserver.actions import projects
from jobserver.utils import set_from_qs
from staff.forms import ProjectEditForm
from tests.factories import (
    AuditableEvent,
    OrgFactory,
    ProjectCollaborationFactory,
    ProjectFactory,
    UserFactory,
)


def test_add_project_with_copilot():
    org1 = OrgFactory()
    org2 = OrgFactory()

    actor = UserFactory()
    copilot = UserFactory()

    project = projects.add(
        name="test",
        number=31337,
        orgs=[org1, org2],
        copilot=copilot,
        by=actor,
    )

    event = AuditableEvent.objects.get(type=AuditableEvent.Type.PROJECT_CREATED)

    assert project.name == "test"
    assert project.number == 31337
    assert project.copilot == copilot
    assert project.created_at
    assert project.created_by == actor
    assert project.updated_at
    assert project.updated_by == actor

    collaboration1, collaboration2 = project.collaborations.all()

    assert collaboration1.org == org1
    assert collaboration1.is_lead
    assert collaboration1.created_at
    assert collaboration1.created_by == actor
    assert collaboration1.updated_at
    assert collaboration1.updated_by == actor

    assert collaboration2.org == org2
    assert not collaboration2.is_lead
    assert collaboration2.created_at
    assert collaboration2.created_by == actor
    assert collaboration2.updated_at
    assert collaboration2.updated_by == actor

    assert event.target_model == project._meta.label
    assert event.target_id == str(project.pk)
    assert event.target_user == actor.username
    assert event.parent_model == project._meta.label
    assert event.parent_id == str(project.pk)
    assert event.created_by == actor.username


def test_add_project_without_copilot():
    org1 = OrgFactory()
    org2 = OrgFactory()

    actor = UserFactory()

    project = projects.add(name="test", number=31337, orgs=[org1, org2], by=actor)

    event = AuditableEvent.objects.get(type=AuditableEvent.Type.PROJECT_CREATED)

    assert project.name == "test"
    assert project.number == 31337
    assert project.copilot is None
    assert project.created_at
    assert project.created_by == actor
    assert project.updated_at
    assert project.updated_by == actor

    collaboration1, collaboration2 = project.collaborations.all()

    assert collaboration1.org == org1
    assert collaboration1.is_lead
    assert collaboration1.created_at
    assert collaboration1.created_by == actor
    assert collaboration1.updated_at
    assert collaboration1.updated_by == actor

    assert collaboration2.org == org2
    assert not collaboration2.is_lead
    assert collaboration2.created_at
    assert collaboration2.created_by == actor
    assert collaboration2.updated_at
    assert collaboration2.updated_by == actor

    assert event.target_model == project._meta.label
    assert event.target_id == str(project.pk)
    assert event.target_user == actor.username
    assert event.parent_model == project._meta.label
    assert event.parent_id == str(project.pk)
    assert event.created_by == actor.username


def test_edit():
    org1 = OrgFactory()
    org2 = OrgFactory()
    org3 = OrgFactory()

    project = ProjectFactory(slug="old")
    ProjectCollaborationFactory(project=project, org=org1, is_lead=True)
    ProjectCollaborationFactory(project=project, org=org2)

    actor = UserFactory()

    form = ProjectEditForm(
        instance=project,
        data={
            "name": project.name,
            "slug": "new",
            "status": project.status,
            "orgs": [
                org1.pk,
                org2.pk,
                org3.pk,
            ],
        },
    )
    assert form.is_valid(), form.errors

    new = projects.edit(old=project, form=form, by=actor)

    assert new.slug == "new"
    assert set_from_qs(new.orgs) == {org1.pk, org2.pk, org3.pk}
