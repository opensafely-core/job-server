from jobserver.authorization import ProjectDeveloper
from jobserver.commands import project_members as members
from jobserver.models import AuditableEvent
from jobserver.utils import set_from_list, set_from_qs
from tests.factories import ProjectFactory, ProjectMembershipFactory, UserFactory


def test_add():
    creator = UserFactory()
    project = ProjectFactory()
    users = UserFactory.create_batch(3)

    for user in users:
        members.add(project=project, user=user, roles=[], by=creator)

    assert project.members.count() == 3
    assert set_from_qs(project.members.all()) == set_from_list(users)

    for membership in project.memberships.all():
        assert membership.roles == []

        event = AuditableEvent.objects.get(target_user=membership.user.username)
        assert event.type == AuditableEvent.Type.PROJECT_MEMBER_ADDED
        assert event.target_model == "jobserver.ProjectMembership"
        assert event.target_id == str(membership.pk)
        assert event.target_user == membership.user.username
        assert event.parent_model == "jobserver.Project"
        assert event.parent_id == str(project.pk)
        assert event.created_by == creator.username
        assert event.created_at


def test_add_with_roles():
    creator = UserFactory()
    project = ProjectFactory()
    users = UserFactory.create_batch(3)

    for user in users:
        members.add(project=project, user=user, roles=[ProjectDeveloper], by=creator)

    assert project.members.count() == 3
    assert set_from_qs(project.members.all()) == set_from_list(users)

    for membership in project.memberships.all():
        assert membership.roles == [ProjectDeveloper]

        added, updated_roles = list(
            AuditableEvent.objects.filter(
                target_user=membership.user.username
            ).order_by("created_at")
        )

        assert added.type == AuditableEvent.Type.PROJECT_MEMBER_ADDED
        assert added.target_model == "jobserver.ProjectMembership"
        assert added.target_id == str(membership.pk)
        assert added.target_user == membership.user.username
        assert added.parent_model == "jobserver.Project"
        assert added.parent_id == str(project.pk)
        assert added.created_by == creator.username
        assert added.created_at

        assert updated_roles.type == AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES
        assert updated_roles.target_model == "jobserver.ProjectMembership"
        assert updated_roles.target_field == "roles"
        assert updated_roles.target_id == str(membership.pk)
        assert updated_roles.target_user == membership.user.username
        assert updated_roles.parent_model == "jobserver.Project"
        assert updated_roles.parent_id == str(project.pk)
        assert updated_roles.new == "jobserver.authorization.roles.ProjectDeveloper"
        assert updated_roles.created_by == creator.username
        assert updated_roles.created_at


def test_update_roles():
    updator = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=user, roles=[])

    assert membership.roles == []

    members.update_roles(member=membership, by=updator, roles=[ProjectDeveloper])

    membership.refresh_from_db()
    assert membership.roles == [ProjectDeveloper]

    assert AuditableEvent.objects.count() == 2

    # first one is the membership we added while staging this test
    event = AuditableEvent.objects.last()

    assert event.type == AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES
    assert event.target_model == "jobserver.ProjectMembership"
    assert event.target_id == str(membership.pk)
    assert event.target_user == user.username
    assert event.parent_model == "jobserver.Project"
    assert event.parent_id == str(project.pk)
    assert event.created_by == updator.username


def test_remove():
    deletor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    membership = ProjectMembershipFactory(project=project, user=user)
    membership_pk = str(membership.pk)

    members.remove(membership=membership, by=deletor)

    assert not project.memberships.exists()

    assert AuditableEvent.objects.count() == 2

    # first one is the membership we added while staging this test
    event = AuditableEvent.objects.last()

    assert event.type == AuditableEvent.Type.PROJECT_MEMBER_REMOVED
    assert event.target_model == "jobserver.ProjectMembership"
    assert event.target_id == membership_pk
    assert event.target_user == user.username
    assert event.parent_model == "jobserver.Project"
    assert event.parent_id == str(project.pk)
    assert event.created_by == deletor.username
