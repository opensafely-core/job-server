from unittest.mock import Mock

import pytest
from django.db import transaction

from jobserver.actions import projects
from jobserver.models import AuditableEvent, Project, ProjectCollaboration
from jobserver.utils import set_from_qs
from redirects.models import Redirect
from tests.factories import (
    OrgFactory,
    ProjectCollaborationFactory,
    ProjectFactory,
    UserFactory,
)


@pytest.mark.django_db(transaction=True)
def test_add_project_with_copilot(monkeypatch):
    org0 = OrgFactory()
    org1 = OrgFactory()

    actor = UserFactory()
    copilot = UserFactory()

    # Mock notifier to avoid testing details of how it works in this unit test.
    mock_notify = Mock()
    monkeypatch.setattr(
        "jobserver.actions.projects.notify_copilots_project_added", mock_notify
    )

    project = projects.add(
        name="test",
        number=31337,
        orgs=[org0, org1],
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

    assert collaboration1.org == org0
    assert collaboration1.is_lead
    assert collaboration1.created_at
    assert collaboration1.created_by == actor
    assert collaboration1.updated_at
    assert collaboration1.updated_by == actor

    assert collaboration2.org == org1
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

    mock_notify.assert_called_once_with(project)


@pytest.mark.django_db(transaction=True)
def test_add_project_without_copilot(monkeypatch):
    org0 = OrgFactory()
    org1 = OrgFactory()

    actor = UserFactory()

    # Mock notifier to avoid testing details of how it works in this unit test.
    mock_notify = Mock()
    monkeypatch.setattr(
        "jobserver.actions.projects.notify_copilots_project_added", mock_notify
    )

    project = projects.add(name="test", number=31337, orgs=[org0, org1], by=actor)

    event = AuditableEvent.objects.get(type=AuditableEvent.Type.PROJECT_CREATED)

    assert project.name == "test"
    assert project.number == 31337
    assert project.copilot is None
    assert project.created_at
    assert project.created_by == actor
    assert project.updated_at
    assert project.updated_by == actor

    collaboration1, collaboration2 = project.collaborations.all()

    assert collaboration1.org == org0
    assert collaboration1.is_lead
    assert collaboration1.created_at
    assert collaboration1.created_by == actor
    assert collaboration1.updated_at
    assert collaboration1.updated_by == actor

    assert collaboration2.org == org1
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

    mock_notify.assert_called_once_with(project)


@pytest.mark.django_db(transaction=True)
def test_add_project_transaction_rollback(monkeypatch):
    """Test that if a database error rolls back the whole transaction, the
    notify function is not called and no new database entries."""
    org0 = OrgFactory()
    org1 = OrgFactory()

    actor = UserFactory()

    mock_notify = Mock()
    monkeypatch.setattr(
        "jobserver.actions.projects.notify_copilots_project_added", mock_notify
    )

    # Force a rollback of the outer transaction after projects.add registers on_commit.
    # This seems simpler than patching to force the action transaction to raise
    # an error when rolling back.
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            projects.add(name="test", number=31337, orgs=[org0, org1], by=actor)
            raise RuntimeError("force rollback")

    assert not mock_notify.called
    assert not AuditableEvent.objects.exists()
    assert not Project.objects.exists()


def assert_only_lead_org(project, org):
    lead_orgs = ProjectCollaboration.objects.filter(project=project, is_lead=True)
    assert {collaboration.org for collaboration in lead_orgs} == {org}


def test_edit_disjoint_orgs():
    """Test edit when completely different orgs are passed in.

    Before, org0 is lead. org1 and org2 are passed in.
    After, org0 is not related, and org1 is lead."""
    org0, org1, org2 = OrgFactory.create_batch(3)

    project = ProjectFactory(slug="old")
    ProjectCollaborationFactory(project=project, org=org0, is_lead=True)
    ProjectCollaborationFactory(project=project, org=org1)
    assert project.org == org0  # cached so cannot test later
    assert_only_lead_org(project, org0)

    actor = UserFactory()

    data = {
        "name": project.name,
        "slug": "new",
        "status": project.status,
        "orgs": [
            org1.pk,
            org2.pk,
        ],
    }

    new = projects.edit(project=project, fields=data, by=actor)

    assert new.slug == "new"
    assert set_from_qs(new.orgs) == {org1.pk, org2.pk}
    assert ProjectCollaboration.objects.count() == 2
    assert_only_lead_org(project, org1)


def test_edit_existing_org():
    """Test edit when an existing org is passed in along with a new one.

    Before, org0 is lead. org1 and org0 are passed in, in that order.
    After, both are related; org0 is still lead; and org1 is not lead."""
    org0 = OrgFactory()
    org1 = OrgFactory()

    project = ProjectFactory(slug="old")
    ProjectCollaborationFactory(project=project, org=org0, is_lead=True)
    ProjectCollaborationFactory(project=project, org=org1)
    assert project.org == org0  # cached so cannot test later
    assert_only_lead_org(project, org0)

    actor = UserFactory()

    data = {
        "name": project.name,
        "slug": "new",
        "status": project.status,
        "orgs": [
            org1.pk,
            org0.pk,
        ],
    }

    new = projects.edit(project=project, fields=data, by=actor)

    assert new.slug == "new"
    assert set_from_qs(new.orgs) == {org0.pk, org1.pk}
    assert ProjectCollaboration.objects.count() == 2
    assert_only_lead_org(project, org0)


def test_edit_unknown_field():
    """Test that edit with an unknown data key raises an appropriate error."""
    project = ProjectFactory()
    actor = UserFactory()
    data = {
        "foo": None,
    }

    with pytest.raises(ValueError, match="Unknown fields"):
        projects.edit(project=project, fields=data, by=actor)


def test_edit_unchanged_slug():
    """Test edit creates no redirect when the updated slug is unchanged."""
    project = ProjectFactory(slug="slug")
    actor = UserFactory()
    data = {
        "slug": "slug",
    }

    returned = projects.edit(project=project, fields=data, by=actor)

    project = Project.objects.get(pk=project.pk)
    assert project == returned
    assert project.slug == "slug"
    assert Redirect.objects.count() == 0


def test_edit_changed_slug():
    """Test edit creates a redirect when the slug is changed."""
    project = ProjectFactory(slug="old slug")
    actor = UserFactory()
    data = {
        "slug": "new slug",
    }
    old_url = project.get_absolute_url()

    returned = projects.edit(project=project, fields=data, by=actor)

    project = Project.objects.get(pk=project.pk)
    assert project == returned
    assert project.slug == "new slug"
    assert Redirect.objects.count() == 1
    redirect = Redirect.objects.first()
    assert redirect.project == project
    assert redirect.created_by == actor
    assert redirect.old_url == old_url


def test_edit_change_to_no_orgs():
    """Test edit handles setting orgs to empty."""
    org0, org1 = OrgFactory.create_batch(2)
    project = ProjectFactory(name="foo")

    ProjectCollaborationFactory(project=project, org=org0, is_lead=True)
    ProjectCollaborationFactory(project=project, org=org1)
    assert project.org == org0  # cached so cannot test later
    assert_only_lead_org(project, org0)

    actor = UserFactory()

    data = {
        "name": "bar",
        "orgs": [],
    }

    returned = projects.edit(project=project, fields=data, by=actor)

    project = Project.objects.get(pk=project.pk)
    assert project == returned
    assert project.name == "bar"
    assert project.orgs.count() == 0
