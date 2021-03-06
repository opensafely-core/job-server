import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pytest
from django.conf import settings
from django.db import DatabaseError
from rest_framework.exceptions import ValidationError

from jobserver.releases import Release, handle_release, hash_files, list_files

from ..factories import BackendFactory, ReleaseFactory, WorkspaceFactory


def raise_error(**kwargs):
    raise DatabaseError("test error")


DEFAULT_MANIFEST = json.dumps({"workspace": "workspace", "repo": "repo"})


def make_release_zip(release_path, manifest=DEFAULT_MANIFEST):
    with TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "file.txt").write_text("test")
        if manifest:
            path = tmp / "metadata" / "manifest.json"
            path.parent.mkdir()
            path.write_text(manifest)

        files = list_files(tmp)
        files_hash = hash_files(tmp, files)

        with ZipFile(release_path, "w") as zf:
            for f in files:
                zf.write(tmp / f, arcname=str(f))

    return files_hash


@pytest.mark.django_db
def test_handle_release_created(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload)

    release, created = handle_release(
        workspace, backend, "user", release_hash, upload.open("rb")
    )
    assert created
    assert release.id == release_hash
    assert release.backend_user == "user"
    assert release.files == ["file.txt", "metadata/manifest.json"]
    assert release.file_path("file.txt").read_text() == "test"
    assert release.manifest == {"workspace": "workspace", "repo": "repo"}


@pytest.mark.django_db
def test_handle_release_already_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload)
    release = ReleaseFactory(
        id=release_hash,
        files=["file.txt", "metadata/manifest.json"],
        backend_user="original",
    )

    release, created = handle_release(
        release.workspace, release.backend, "user", release_hash, upload.open("rb")
    )
    assert not created
    assert release.id == release_hash
    assert release.backend_user == "original"
    assert release.files == ["file.txt", "metadata/manifest.json"]


@pytest.mark.django_db
def test_handle_release_bad_hash(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload)
    release = ReleaseFactory(
        id=release_hash, files=["file.txt"], backend_user="original"
    )

    with pytest.raises(ValidationError) as exc:
        handle_release(
            release.workspace, release.backend, "user", "bad hash", upload.open("rb")
        )

    assert "did not match" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_no_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload, manifest=None)
    release = ReleaseFactory(
        id=release_hash, files=["file.txt"], backend_user="original"
    )

    with pytest.raises(ValidationError) as exc:
        handle_release(
            release.workspace, release.backend, "user", "bad hash", upload.open("rb")
        )

    assert "file not found" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_bad_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload, manifest="BADJSON")
    release = ReleaseFactory(
        id=release_hash, files=["file.txt"], backend_user="original"
    )

    with pytest.raises(ValidationError) as exc:
        handle_release(
            release.workspace, release.backend, "user", "bad hash", upload.open("rb")
        )

    assert "not valid json" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_db_error(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")
    monkeypatch.setattr(Release.objects, "create", raise_error)

    upload = tmp_path / "release.zip"
    release_hash = make_release_zip(upload)
    workspace = WorkspaceFactory()
    backend = BackendFactory()

    with pytest.raises(DatabaseError):
        handle_release(workspace, backend, "user", release_hash, upload.open("rb"))

    # check the extracted files have been deleted due to the error
    upload_dir = tmp_path / "releases" / workspace.name / release_hash
    assert not upload_dir.exists()


def test_hash_files(tmp_path):
    dirpath = tmp_path / "test"
    dirpath.mkdir()
    files = {
        "foo.txt": "foo",
        "dir/bar.txt": "bar",
        "outputs/data.csv": "data",
    }

    for name, contents in files.items():
        path = dirpath / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(contents)

    assert (
        hash_files(dirpath, list_files(dirpath)) == "6c52ca16d696574e6ab5ece283eb3f3d"
    )
