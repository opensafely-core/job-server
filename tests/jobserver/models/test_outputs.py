import pytest
from django.conf import settings
from django.urls import reverse

from tests.factories import (
    PublicReleaseFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_publicrelease_str():
    user = UserFactory()
    public_release = PublicReleaseFactory(status="derp", created_by=user)

    assert str(public_release) == f"derp Public Release made by {user.username}"


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
