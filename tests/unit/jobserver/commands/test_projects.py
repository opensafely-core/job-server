from jobserver.commands import projects
from tests.factories import OrgFactory, UserFactory


def test_add_interactive_project():
    org1 = OrgFactory()
    org2 = OrgFactory()

    actor = UserFactory()
    copilot = UserFactory()

    project = projects.add(
        name="test",
        number=31337,
        orgs=[org1, org2],
        copilot=copilot,
        application_url="http://example.com",
        by=actor,
    )

    assert project.name == "test"
    assert project.number == 31337
    assert project.copilot == copilot
    assert project.application_url == "http://example.com"
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


def test_add_standard_project():
    org1 = OrgFactory()
    org2 = OrgFactory()

    actor = UserFactory()

    project = projects.add(name="test", number=31337, orgs=[org1, org2], by=actor)

    assert project.name == "test"
    assert project.number == 31337
    assert project.copilot is None
    assert project.application_url == ""
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
