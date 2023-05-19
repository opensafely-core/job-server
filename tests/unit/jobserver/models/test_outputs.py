import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import Snapshot, SnapshotPublishRequest
from jobserver.utils import set_from_qs
from tests.factories import (
    ReleaseFactory,
    ReleaseFileFactory,
    ReleaseFileReviewFactory,
    SnapshotFactory,
    SnapshotPublishRequestFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.utils import minutes_ago


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_release_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFactory(**{field: None})


def test_release_get_absolute_url():
    release = ReleaseFactory()

    url = release.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_get_api_url():
    release = ReleaseFactory()

    assert release.get_api_url() == f"/api/v2/releases/release/{release.id}"


def test_release_get_download_url():
    release = ReleaseFactory()

    url = release.get_download_url()

    assert url == reverse(
        "release-download",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_ulid():
    assert ReleaseFactory().ulid.timestamp


def test_releasefile_absolute_path(release):
    rfile = release.files.first()

    expected = (
        settings.RELEASE_STORAGE
        / release.workspace.name
        / "releases"
        / release.id
        / "file1.txt"
    )
    path = rfile.absolute_path()
    assert path == expected
    assert path.read_text()


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_releasefile_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFileFactory(**{field: None})


def test_releasefile_constraints_deleted_at_and_deleted_by_both_set():
    ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=UserFactory())


def test_releasefile_constraints_deleted_at_and_deleted_by_neither_set():
    ReleaseFileFactory(deleted_at=None, deleted_by=None)


@pytest.mark.django_db(transaction=True)
def test_releasefile_constraints_missing_deleted_at_or_deleted_by():
    with pytest.raises(IntegrityError):
        ReleaseFileFactory(deleted_at=None, deleted_by=UserFactory())

    with pytest.raises(IntegrityError):
        ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=None)


def test_releasefile_get_absolute_url():
    rfile = ReleaseFileFactory(name="file1.txt")

    url = rfile.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "org_slug": rfile.release.workspace.project.org.slug,
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "pk": rfile.release.id,
            "path": rfile.name,
        },
    )


def test_releasefile_get_delete_url():
    rfile = ReleaseFileFactory()

    url = rfile.get_delete_url()

    assert url == reverse(
        "release-file-delete",
        kwargs={
            "org_slug": rfile.release.workspace.project.org.slug,
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "pk": rfile.release.id,
            "release_file_id": rfile.pk,
        },
    )


def test_releasefile_get_latest_url():
    rfile = ReleaseFileFactory(name="file1.txt")

    url = rfile.get_latest_url()

    assert url == reverse(
        "workspace-latest-outputs-detail",
        kwargs={
            "org_slug": rfile.release.workspace.project.org.slug,
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "path": f"{rfile.release.backend.slug}/{rfile.name}",
        },
    )


def test_releasefile_get_api_url_without_is_published():
    rfile = ReleaseFileFactory()

    url = rfile.get_api_url()

    assert url == reverse("api:release-file", kwargs={"file_id": rfile.id})


def test_releasefile_get_api_url_with_is_published():
    rfile = ReleaseFileFactory()

    # mirror the SnapshotAPI view setting this value on the ReleaseFile object.
    setattr(rfile, "is_published", True)

    url = rfile.get_api_url()

    assert url == reverse(
        "published-file",
        kwargs={
            "org_slug": rfile.workspace.project.org.slug,
            "project_slug": rfile.workspace.project.slug,
            "workspace_slug": rfile.workspace.name,
            "file_id": rfile.id,
        },
    )


def test_releasefile_ulid():
    assert ReleaseFileFactory().ulid.timestamp


def test_releasefile_format():
    rfile = ReleaseFileFactory()
    rfile.size = 3.2 * 1024 * 1024  # 3.2Mb
    rfile.save()

    assert f"{rfile:b}" == "3,355,443.2b"
    assert f"{rfile:Kb}" == "3,276.8Kb"
    assert f"{rfile:Mb}" == "3.2Mb"
    assert f"{rfile}".startswith("ReleaseFile object")


def test_releasefilepublishrequest_approve_configured_now():
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = SnapshotPublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    dt = minutes_ago(timezone.now(), 3)

    request.approve(user=user, now=dt)

    request.refresh_from_db()
    assert request.decision_at == dt


def test_releasefilepublishrequest_approve_default_now(freezer):
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = SnapshotPublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    request.approve(user=user)

    request.refresh_from_db()
    assert request.decision_at == timezone.now()
    assert request.decision_by == user
    assert request.decision == SnapshotPublishRequest.Decisions.APPROVED


def test_releasefilepublishrequest_create_from_files_success():
    rfile = ReleaseFileFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    request = SnapshotPublishRequest.create_from_files(
        files=[rfile], user=user, workspace=workspace
    )

    assert request.created_by == user
    assert set_from_qs(request.snapshot.files.all()) == {rfile.pk}


def test_releasefilepublishrequest_create_from_files_with_duplicate_files():
    rfile = ReleaseFileFactory()
    workspace = WorkspaceFactory()

    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.add(rfile)

    user = UserFactory()

    with pytest.raises(Snapshot.DuplicateSnapshotError):
        SnapshotPublishRequest.create_from_files(
            files=[rfile], user=user, workspace=workspace
        )


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_releasefilereview_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFileReviewFactory(**{field: None})


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
            "org_slug": snapshot.workspace.project.org.slug,
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
            "org_slug": snapshot.workspace.project.org.slug,
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

    SnapshotPublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=SnapshotPublishRequest.Decisions.APPROVED,
    )

    assert snapshot.is_published


def test_snapshot_str():
    user = UserFactory()

    snapshot = SnapshotFactory(created_by=user)
    SnapshotPublishRequestFactory(
        snapshot=snapshot,
        decision=SnapshotPublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=user,
    )
    assert str(snapshot) == f"Published Snapshot made by {user.username}"

    snapshot = SnapshotFactory(created_by=user)
    assert str(snapshot) == f"Draft Snapshot made by {user.username}"
