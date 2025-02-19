from interactive.commands import create_user
from jobserver.authorization import InteractiveReporter
from jobserver.models import AuditableEvent
from jobserver.utils import set_from_qs

from ...factories import (
    OrgFactory,
    ProjectFactory,
    UserFactory,
)


def test_create_user():
    creator = UserFactory()
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])

    user = create_user(
        creator=creator,
        email="test@example.com",
        name="Testing McTesterson",
        project=project,
    )

    assert user.created_by == creator
    assert user.name == "Testing McTesterson"
    assert user.email == "test@example.com"
    assert set_from_qs(user.orgs.all()) == set_from_qs(project.orgs.all())
    assert set_from_qs(user.projects.all()) == {project.pk}

    assert user.project_memberships.first().roles == [InteractiveReporter]

    assert AuditableEvent.objects.count() == 2

    # light touch sense check that we're creating the right type of event, the
    # tests for members.add will check all the relevant parts of the event
    first, second = AuditableEvent.objects.all()
    assert first.type == AuditableEvent.Type.PROJECT_MEMBER_ADDED
    assert second.type == AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES
