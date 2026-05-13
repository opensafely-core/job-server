from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from jobserver.models import PublishRequest
from tests.factories import (
    PublishRequestFactory,
    ReleaseFileFactory,
    SnapshotFactory,
    UserFactory,
)


def test_remove_files_from_publish_request_unknown_snapshot():
    snapshot_id = -1

    with pytest.raises(CommandError, match=f"Unknown snapshot: {snapshot_id}"):
        call_command("remove_files_from_publish_request", snapshot_id, "/dummy/path")


def test_remove_files_from_publish_request_unknown_path():
    snapshot = SnapshotFactory()
    release_file = ReleaseFileFactory(
        workspace=snapshot.workspace, name="/release/test/file.csv"
    )
    snapshot.files.add(release_file)

    with pytest.raises(CommandError, match="Unknown file path: /dummy/path"):
        call_command(
            "remove_files_from_publish_request",
            snapshot.id,
            release_file.name,
            "/dummy/path",
        )


def test_remove_files_from_publish_request_path_to_file_not_in_snapshot():
    snapshot = SnapshotFactory()
    release_file = ReleaseFileFactory(name="/release/test/file.csv")

    with pytest.raises(CommandError, match=f"Unknown file path: {release_file.name}"):
        call_command(
            "remove_files_from_publish_request",
            snapshot.id,
            release_file.name,
        )


def test_remove_files_from_publish_request_published():
    publish_request = PublishRequestFactory(
        decision=PublishRequest.Decisions.APPROVED,
        decision_by=UserFactory(),
        decision_at=datetime.now(UTC),
    )

    with pytest.raises(
        CommandError,
        match=(
            f"Snapshot {publish_request.snapshot.id} has been published and cannot be edited"
        ),
    ):
        call_command(
            "remove_files_from_publish_request",
            publish_request.snapshot.id,
            "/dummy/path",
        )


def test_remove_files_from_publish_request(n_to_remove=2):
    out = StringIO()
    err = StringIO()

    snapshot = SnapshotFactory()
    release_file_to_keep = ReleaseFileFactory(
        workspace=snapshot.workspace, name="/release/test/file_to_keep.csv"
    )
    release_files_to_remove = [
        ReleaseFileFactory(
            workspace=snapshot.workspace, name=f"/release/test/file_to_remove-{n}.csv"
        )
        for n in range(0, n_to_remove)
    ]

    snapshot.files.add(release_file_to_keep)
    for release_file_to_remove in release_files_to_remove:
        snapshot.files.add(release_file_to_remove)

    assert snapshot.files.count() == 1 + n_to_remove
    assert release_file_to_keep in snapshot.files.all()
    assert all(
        [
            release_file_to_remove in snapshot.files.all()
            for release_file_to_remove in release_files_to_remove
        ]
    )

    call_command(
        "remove_files_from_publish_request",
        snapshot.id,
        *[
            release_file_to_remove.name
            for release_file_to_remove in release_files_to_remove
        ],
        stdout=out,
        stderr=err,
    )

    assert not err.getvalue()
    assert snapshot.files.count() == 1
    assert release_file_to_keep in snapshot.files.all()
    assert all(
        [
            release_file_to_remove not in snapshot.files.all()
            for release_file_to_remove in release_files_to_remove
        ]
    )

    assert f"{n_to_remove} files removed from" in out.getvalue()


def test_remove_files_from_publish_request_ignores_duplicate_path_outside_snapshot():
    out = StringIO()
    err = StringIO()

    path = "/release/test/file.csv"
    snapshot = SnapshotFactory()
    release_file_to_remove = ReleaseFileFactory(workspace=snapshot.workspace, name=path)
    duplicate_release_file = ReleaseFileFactory(workspace=snapshot.workspace, name=path)

    snapshot.files.add(release_file_to_remove)

    call_command(
        "remove_files_from_publish_request",
        snapshot.id,
        path,
        stdout=out,
        stderr=err,
    )

    assert not err.getvalue()
    assert release_file_to_remove not in snapshot.files.all()
    assert duplicate_release_file not in snapshot.files.all()
    assert "1 files removed from" in out.getvalue()
