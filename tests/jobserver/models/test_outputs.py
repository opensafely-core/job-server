import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from tests.factories import (
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
)


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_release_get_api_url():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    assert release.get_api_url() == f"/api/v2/releases/release/{release.id}"


@pytest.mark.django_db
def test_release_ulid():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    assert release.ulid.timestamp


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_releasefile_ulid():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()
    assert rfile.ulid.timestamp


@pytest.mark.django_db
def test_snapshot_str():
    user = UserFactory()

    snapshot = SnapshotFactory(created_by=user, published_at=timezone.now())
    assert str(snapshot) == f"Published Snapshot made by {user.username}"

    snapshot = SnapshotFactory(created_by=user)
    assert str(snapshot) == f"Draft Snapshot made by {user.username}"


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_snapshot_is_draft():
    assert SnapshotFactory(published_at=None).is_draft


@pytest.mark.django_db
def test_snapshot_is_published():
    assert SnapshotFactory(published_at=timezone.now()).is_published
