import pytest
from django.utils import timezone

from jobserver.models import PublishRequest, Snapshot
from jobserver.utils import set_from_qs
from tests.factories import (
    PublishRequestFactory,
    ReleaseFileFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.utils import minutes_ago


def test_publishrequest_approve_configured_now():
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = PublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    dt = minutes_ago(timezone.now(), 3)

    request.approve(user=user, now=dt)

    request.refresh_from_db()
    assert request.decision_at == dt


def test_publishrequest_approve_default_now(freezer):
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = PublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    now = timezone.now()
    freezer.move_to(now)

    request.approve(user=user)

    request.refresh_from_db()
    assert request.decision_at == now
    assert request.decision_by == user
    assert request.decision == PublishRequest.Decisions.APPROVED


def test_publishrequest_create_from_files_success():
    workspace = WorkspaceFactory()
    rfile = ReleaseFileFactory(workspace=workspace)
    user = UserFactory()

    request = PublishRequest.create_from_files(files=[rfile], user=user)

    assert request.created_by == user
    assert set_from_qs(request.snapshot.files.all()) == {rfile.pk}


def test_publishrequest_create_from_files_with_duplicate_files():
    workspace = WorkspaceFactory()
    rfile = ReleaseFileFactory(workspace=workspace)

    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.add(rfile)

    user = UserFactory()

    publish_request = PublishRequest.create_from_files(files=[rfile], user=user)

    assert publish_request.snapshot == snapshot


def test_publishrequest_create_from_files_with_existing_publish_request():
    workspace = WorkspaceFactory()
    files = ReleaseFileFactory.create_batch(3, workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(files)
    user = UserFactory()

    publish_request = PublishRequestFactory(snapshot=snapshot, created_by=user)

    output = PublishRequest.create_from_files(files=files, user=user)

    assert output == publish_request


def test_publishrequest_create_from_files_with_existing_snapshot():
    workspace = WorkspaceFactory()
    files = ReleaseFileFactory.create_batch(3, workspace=workspace)

    snapshot1 = SnapshotFactory(workspace=workspace)
    snapshot1.files.set(files)

    snapshot2 = SnapshotFactory(workspace=workspace)
    snapshot2.files.set(files)

    with pytest.raises(Snapshot.MultipleObjectsReturned):
        PublishRequest.create_from_files(files=files, user=UserFactory())


def test_publishrequest_create_from_files_with_multiple_workspaces():
    user = UserFactory()

    rfiles = [
        ReleaseFileFactory(workspace=WorkspaceFactory()),
        ReleaseFileFactory(workspace=WorkspaceFactory()),
    ]

    with pytest.raises(PublishRequest.MultipleWorkspacesFound):
        PublishRequest.create_from_files(files=rfiles, user=user)


def test_publishrequest_is_approved():
    publish_request = PublishRequestFactory(
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    assert publish_request.is_approved


def test_publishrequest_is_pending():
    assert PublishRequestFactory().is_pending


def test_publishrequest_is_rejected():
    publish_request = PublishRequestFactory(
        decision=PublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    assert publish_request.is_rejected


def test_publishrequest_reject(freezer):
    request = PublishRequestFactory()
    user = UserFactory()

    now = timezone.now()
    freezer.move_to(now)

    request.reject(user=user)

    request.refresh_from_db()
    assert request.decision_at == now
    assert request.decision_by == user
    assert request.decision == PublishRequest.Decisions.REJECTED


def test_publishrequest_str():
    snapshot = SnapshotFactory()
    publish_request = PublishRequestFactory(snapshot=snapshot)

    assert str(publish_request) == f"Publish request for Snapshot={snapshot.pk}"
