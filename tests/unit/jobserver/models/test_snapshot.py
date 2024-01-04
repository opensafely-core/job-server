import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import PublishRequest
from tests.factories import (
    PublishRequestFactory,
    SnapshotFactory,
    UserFactory,
)


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_snapshot_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        SnapshotFactory(**{field: None})


def test_snapshot_get_absolute_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_absolute_url()

    assert url == reverse(
        "workspace-snapshot-detail",
        kwargs={
            "project_slug": snapshot.workspace.project.slug,
            "workspace_slug": snapshot.workspace.name,
            "pk": snapshot.pk,
        },
    )


def test_snapshot_get_api_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_api_url()

    assert url == reverse(
        "api:snapshot",
        kwargs={
            "workspace_id": snapshot.workspace.name,
            "snapshot_id": snapshot.pk,
        },
    )


def test_snapshot_get_download_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_download_url()

    assert url == reverse(
        "workspace-snapshot-download",
        kwargs={
            "project_slug": snapshot.workspace.project.slug,
            "workspace_slug": snapshot.workspace.name,
            "pk": snapshot.pk,
        },
    )


def test_snapshot_get_publish_api_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_publish_api_url()

    assert url == reverse(
        "api:snapshot-publish",
        kwargs={
            "workspace_id": snapshot.workspace.name,
            "snapshot_id": snapshot.pk,
        },
    )


def test_snapshot_is_draft():
    assert SnapshotFactory().is_draft


def test_snapshot_is_published():
    snapshot = SnapshotFactory()

    PublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    assert snapshot.is_published


def test_snapshot_str():
    user = UserFactory()

    snapshot = SnapshotFactory(created_by=user)
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=user,
    )
    assert str(snapshot) == f"Published Snapshot made by {user.username}"

    snapshot = SnapshotFactory(created_by=user)
    assert str(snapshot) == f"Draft Snapshot made by {user.username}"
