from datetime import timedelta

import pytest
from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from jobserver.releases import Release, handle_release, hash_files, workspace_files

from ..factories import (
    BackendFactory,
    ReleaseFactory,
    ReleaseUploadFactory,
    WorkspaceFactory,
)


def raise_error(**kwargs):
    raise DatabaseError("test error")


@pytest.mark.django_db
def test_handle_release_created():
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    upload = ReleaseUploadFactory()

    release, created = handle_release(
        workspace,
        backend,
        "user",
        upload.hash,
        upload.zip,
    )
    assert created
    assert release.id == upload.hash
    assert release.backend_user == "user"
    assert release.files.count() == 1
    assert release.files.first().name == "file.txt"
    assert (
        release.files.first().path
        == f"{workspace.name}/releases/{upload.hash}/file.txt"
    )
    assert release.manifest == {"workspace": "workspace", "repo": "repo"}


@pytest.mark.django_db
def test_handle_release_already_exists():

    files = {"file.txt": "mydata"}
    existing_release = ReleaseFactory(
        files=files,
        backend_user="original",
    )
    upload = ReleaseUploadFactory(files=files)

    # check out test setup is correct
    assert existing_release.id == upload.hash

    # upload same files
    release, created = handle_release(
        existing_release.workspace,
        existing_release.backend,
        "user",
        upload.hash,
        upload.zip,
    )
    assert not created
    assert release.id == existing_release.id
    assert release.backend_user == "original"  # Not 'user'
    assert release.files.count() == 1
    assert release.files.first().name == "file.txt"


@pytest.mark.django_db
def test_handle_release_bad_hash():
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    upload = ReleaseUploadFactory()

    with pytest.raises(ValidationError) as exc:
        handle_release(
            workspace,
            backend,
            "user",
            "bad hash",
            upload.zip,
        )

    assert "did not match" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_no_manifest():
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    upload = ReleaseUploadFactory(manifest=None)

    with pytest.raises(ValidationError) as exc:
        handle_release(
            workspace,
            backend,
            "user",
            upload.hash,
            upload.zip,
        )

    assert "file not found" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_bad_manifest():
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    upload = ReleaseUploadFactory(raw_manifest="BADJSON")

    with pytest.raises(ValidationError) as exc:
        handle_release(
            workspace,
            backend,
            "user",
            upload.hash,
            upload.zip,
        )

    assert "not valid json" in exc.value.detail["detail"]


@pytest.mark.django_db
def test_handle_release_db_error(monkeypatch):
    workspace = WorkspaceFactory()
    backend = BackendFactory()
    upload = ReleaseUploadFactory()

    monkeypatch.setattr(Release.objects, "create", raise_error)
    with pytest.raises(DatabaseError):
        handle_release(workspace, backend, "user", upload.hash, upload.zip)

    # check the extracted files have been deleted due to the error
    upload_dir = settings.RELEASE_STORAGE / workspace.name / upload.hash
    assert not upload_dir.exists()


def test_hash_files(tmp_path):
    dirpath = tmp_path / "test"
    dirpath.mkdir()
    files = {
        "foo.txt": "foo",
        "dir/bar.txt": "bar",
        "outputs/data.csv": "data",
        "metadata/manifest.json": '{"foo":"bar"}',
    }

    for name, contents in files.items():
        path = dirpath / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(contents)

    release_hash, release_files = hash_files(dirpath)
    assert "metadata/manifest.json" not in release_files
    assert release_hash == "6c52ca16d696574e6ab5ece283eb3f3d"


@pytest.mark.django_db
def test_workspace_files_no_releases():
    workspace = WorkspaceFactory()

    assert workspace_files(workspace) == {}


@pytest.mark.django_db
def test_workspace_files_one_release():
    backend = BackendFactory(name="backend")
    workspace = WorkspaceFactory()
    release = ReleaseFactory(
        workspace=workspace, backend=backend, files=["test1", "test2", "test3"]
    )

    output = workspace_files(workspace)

    assert output == {
        "backend/test1": release.files.get(name="test1"),
        "backend/test2": release.files.get(name="test2"),
        "backend/test3": release.files.get(name="test3"),
    }


@pytest.mark.django_db
def test_workspace_files_many_releases(freezer):
    now = timezone.now()

    backend1 = BackendFactory(name="backend1")
    backend2 = BackendFactory(name="backend2")
    workspace = WorkspaceFactory()

    def minutes_ago(minutes):
        return now - timedelta(minutes=minutes)

    ReleaseFactory(
        workspace=workspace,
        backend=backend1,
        files=["test1", "test2", "test3"],
        created_at=minutes_ago(10),
    )
    ReleaseFactory(
        workspace=workspace,
        backend=backend1,
        files=["test2", "test3"],
        created_at=minutes_ago(8),
    )
    release3 = ReleaseFactory(
        workspace=workspace,
        backend=backend1,
        files=["test2"],
        created_at=minutes_ago(6),
    )
    release4 = ReleaseFactory(
        workspace=workspace,
        backend=backend1,
        files=["test1", "test3"],
        created_at=minutes_ago(4),
    )
    release5 = ReleaseFactory(
        workspace=workspace,
        backend=backend1,
        files=["test1"],
        created_at=minutes_ago(2),
    )
    # different backend, same file name, more recent
    release6 = ReleaseFactory(
        workspace=workspace,
        backend=backend2,
        files={"test1": "content"},
        created_at=minutes_ago(1),
    )

    output = workspace_files(workspace)

    assert output == {
        "backend1/test1": release5.files.get(name="test1"),
        "backend1/test3": release4.files.get(name="test3"),
        "backend1/test2": release3.files.get(name="test2"),
        "backend2/test1": release6.files.get(name="test1"),
    }
