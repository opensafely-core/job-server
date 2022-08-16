import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from tests.factories import (
    ReleaseFactory,
    ReleaseFileFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
)


def test_release_get_absolute_url():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))

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
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    assert release.get_api_url() == f"/api/v2/releases/release/{release.id}"


def test_release_get_download_url():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))

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
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    assert release.ulid.timestamp


def test_release_file_absolute_path():
    files = {"file.txt": b"test_absolute_path"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))
    rfile = release.files.get(name="file.txt")

    expected = (
        settings.RELEASE_STORAGE
        / f"{release.workspace.name}/releases/{release.id}/file.txt"
    )
    path = rfile.absolute_path()
    assert path == expected
    assert path.read_text() == "test_absolute_path"


def test_releasefile_constraints_deleted_at_and_deleted_by_both_set():
    upload = ReleaseUploadsFactory({"file1.txt": b"test"})[0]
    ReleaseFileFactory(upload, deleted_at=timezone.now(), deleted_by=UserFactory())


def test_releasefile_constraints_deleted_at_and_deleted_by_neither_set():
    upload = ReleaseUploadsFactory({"file1.txt": b"test"})[0]
    ReleaseFileFactory(upload, deleted_at=None, deleted_by=None)


@pytest.mark.django_db(transaction=True)
def test_releasefile_constraints_missing_deleted_at_or_deleted_by():
    upload = ReleaseUploadsFactory({"file1.txt": b"test"})[0]

    with pytest.raises(IntegrityError):
        ReleaseFileFactory(upload, deleted_at=None, deleted_by=UserFactory())

    with pytest.raises(IntegrityError):
        ReleaseFileFactory(upload, deleted_at=timezone.now(), deleted_by=None)


def test_releasefile_get_absolute_url():
    files = {"file.txt": b"contents"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))

    file = release.files.first()

    url = file.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
            "path": file.name,
        },
    )


def test_releasefile_get_delete_url():
    files = {"file.txt": b"contents"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))

    file = release.files.first()

    url = file.get_delete_url()

    assert url == reverse(
        "release-file-delete",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
            "release_file_id": file.pk,
        },
    )


def test_releasefile_get_latest_url():
    files = {"file.txt": b"contents"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))

    file = release.files.first()

    url = file.get_latest_url()

    assert url == reverse(
        "workspace-latest-outputs-detail",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "path": f"{release.backend.slug}/{file.name}",
        },
    )


def test_releasefile_get_api_url_without_is_published():
    files = {"file.txt": b"contents"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))

    file = release.files.first()

    url = file.get_api_url()

    assert url == reverse("api:release-file", kwargs={"file_id": file.id})


def test_releasefile_get_api_url_with_is_published():
    files = {"file.txt": b"contents"}
    release = ReleaseFactory(ReleaseUploadsFactory(files))

    file = release.files.first()

    # mirror the SnapshotAPI view setting this value on the ReleaseFile object.
    setattr(file, "is_published", True)

    url = file.get_api_url()

    assert url == reverse(
        "published-file",
        kwargs={
            "org_slug": release.workspace.project.org.slug,
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "file_id": file.id,
        },
    )


def test_releasefile_ulid():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()
    assert rfile.ulid.timestamp


def test_releasefile_format():
    release = ReleaseFactory(ReleaseUploadsFactory({"file1.txt": b"a"}))

    rfile = release.files.first()
    rfile.size = 3.2 * 1024 * 1024  # 3.2Mb
    rfile.save()

    assert f"{rfile:b}" == "3,355,443.2b"
    assert f"{rfile:Kb}" == "3,276.8Kb"
    assert f"{rfile:Mb}" == "3.2Mb"
    assert f"{rfile}".startswith("ReleaseFile object")


def test_snapshot_str():
    user = UserFactory()

    snapshot = SnapshotFactory(created_by=user, published_at=timezone.now())
    assert str(snapshot) == f"Published Snapshot made by {user.username}"

    snapshot = SnapshotFactory(created_by=user)
    assert str(snapshot) == f"Draft Snapshot made by {user.username}"


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
    assert SnapshotFactory(published_at=None).is_draft


def test_snapshot_is_published():
    assert SnapshotFactory(published_at=timezone.now()).is_published
