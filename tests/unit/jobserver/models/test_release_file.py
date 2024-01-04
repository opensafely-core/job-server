import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from tests.factories import ReleaseFileFactory, UserFactory


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


def test_releasefile_format():
    size = 3.2 * 1024 * 1024  # 3.2Mb
    rfile = ReleaseFileFactory(name="important/research.html", size=size)

    assert f"{rfile:b}" == "3,355,443.2b"
    assert f"{rfile:Kb}" == "3,276.8Kb"
    assert f"{rfile:Mb}" == "3.2Mb"
    assert f"{rfile}".startswith("important/research.html")


def test_releasefile_get_absolute_url():
    rfile = ReleaseFileFactory(name="file1.txt")

    url = rfile.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
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
            "project_slug": rfile.workspace.project.slug,
            "workspace_slug": rfile.workspace.name,
            "file_id": rfile.id,
        },
    )


def test_releasefile_str():
    rfile = ReleaseFileFactory(id="12345", name="important/research.html")

    assert str(rfile) == "important/research.html (12345)"


def test_releasefile_ulid():
    assert ReleaseFileFactory().ulid.timestamp
