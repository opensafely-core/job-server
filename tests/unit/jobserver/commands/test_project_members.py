import pytest
from django.db import IntegrityError

from jobserver.authorization import ProjectDeveloper
from jobserver.commands import project_members as members
from jobserver.models import AuditableEvent, ProjectMembership
from jobserver.utils import set_from_list, set_from_qs
from tests.factories import ProjectFactory, UserFactory


def raise_integrity_error(*args, **kwargs):
    raise IntegrityError


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


def test_add_with_integrity_error(monkeypatch):
    project = ProjectFactory()
    user, creator = UserFactory.create_batch(2)

    assert ProjectMembership.objects.count() == 0
    assert AuditableEvent.objects.count() == 0

    with monkeypatch.context() as mp, pytest.raises(IntegrityError):
        # We patch AuditableEvent.objects.create because it is called after
        # Project.memberships.create. In other words, we test that a ProjectMembership
        # isn't created if creating an AuditableEvent fails.
        mp.setattr(
            "jobserver.models.AuditableEvent.objects.create", raise_integrity_error
        )
        members.add(project=project, user=user, roles=[], by=creator)

    # nothing has changed
    assert ProjectMembership.objects.count() == 0
    assert AuditableEvent.objects.count() == 0


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


def test_update_roles(project_membership):
    updator = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    membership = project_membership(project=project, user=user, roles=[])

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


def test_update_roles_with_integrity_error(monkeypatch, project_membership):
    project = ProjectFactory()
    user, updator = UserFactory.create_batch(2)
    membership = project_membership(project=project, user=user, roles=[])

    assert ProjectMembership.objects.count() == 1
    assert AuditableEvent.objects.count() == 1

    with monkeypatch.context() as mp, pytest.raises(IntegrityError):
        # We patch ProjectMembership.save because it is called after
        # AuditableEvent.objects.create. In other words, we test that an AuditableEvent
        # isn't created if updating a ProjectMembership fails.
        mp.setattr("jobserver.models.ProjectMembership.save", raise_integrity_error)
        members.update_roles(member=membership, by=updator, roles=[ProjectDeveloper])

    # nothing has changed
    assert ProjectMembership.objects.count() == 1
    assert AuditableEvent.objects.count() == 1


def test_remove(project_membership):
    deletor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    membership = project_membership(project=project, user=user)
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


def test_remove_with_integrity_error(monkeypatch, project_membership):
    project = ProjectFactory()
    user, deletor = UserFactory.create_batch(2)
    membership = project_membership(project=project, user=user, roles=[])

    assert ProjectMembership.objects.count() == 1
    assert AuditableEvent.objects.count() == 1

    with monkeypatch.context() as mp, pytest.raises(IntegrityError):
        # We patch ProjectMembership.delete because it is called after
        # AuditableEvent.objects.create. In other words, we test that an AuditableEvent
        # isn't created if deleting a ProjectMembership fails.
        mp.setattr("jobserver.models.ProjectMembership.delete", raise_integrity_error)
        members.remove(membership=membership, by=deletor)

    # nothing has changed
    assert ProjectMembership.objects.count() == 1
    assert AuditableEvent.objects.count() == 1
