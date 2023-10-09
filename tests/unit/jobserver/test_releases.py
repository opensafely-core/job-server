import hashlib
import io
import zipfile
from datetime import timedelta

import pytest
from django.db import DatabaseError
from django.utils import timezone
from rest_framework.exceptions import NotFound

from jobserver import releases
from jobserver.models import ReleaseFile
from jobserver.models.outputs import absolute_file_path
from tests.factories import (
    BackendFactory,
    ReleaseFileFactory,
    UserFactory,
    WorkspaceFactory,
)

from ...utils import minutes_ago


def raise_error(**kwargs):
    raise DatabaseError("test error")


def test_build_hatch_token_and_url_default():
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    releases.build_hatch_token_and_url(
        backend=backend,
        workspace=workspace,
        user=user,
    )


def test_build_hatch_token_and_url_with_custom_expires():
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    releases.build_hatch_token_and_url(
        backend=backend,
        workspace=workspace,
        user=user,
        expiry=timezone.now() + timedelta(minutes=3),
    )


def test_build_outputs_zip(release):
    zf = releases.build_outputs_zip(release.files.all(), None)

    with zipfile.ZipFile(zf, "r") as zip_obj:
        assert zip_obj.testzip() is None

        assert zip_obj.namelist() == ["file1.txt"]

        with open(release.files.first().absolute_path(), "rb") as f:
            original_contents = f.read()

        with zip_obj.open("file1.txt") as f:
            zipped_contents = f.read()

        # check the zipped files contents match the original files contents
        assert zipped_contents == original_contents


def test_build_outputs_zip_with_missing_files(build_release_with_files):
    release = build_release_with_files(["test1", "test3", "test5"])

    # create a couple of deleted files
    user = UserFactory()
    ReleaseFileFactory(
        release=release, name="test2", deleted_at=timezone.now(), deleted_by=user
    )
    ReleaseFileFactory(
        release=release, name="test4", deleted_at=timezone.now(), deleted_by=user
    )

    release.requested_files.append([{"name": "test2"}, {"name": "test4"}])
    files = release.files.order_by("name")

    zf = releases.build_outputs_zip(files, lambda u: u)

    with zipfile.ZipFile(zf, "r") as zip_obj:
        assert zip_obj.testzip() is None

        assert zip_obj.namelist() == ["test1", "test2", "test3", "test4", "test5"]

        # check ReleaseFile on-disk contents matches their zipped contents
        for name in ["test1", "test3", "test5"]:
            with open(files.get(name=name).absolute_path(), "rb") as f:
                original_contents = f.read()

            with zip_obj.open(name) as f:
                zipped_contents = f.read()

            assert zipped_contents == original_contents

        for name in ["test2", "test4"]:
            with zip_obj.open(name) as f:
                zipped_contents = f.read().decode()

            rfile = files.get(name=name)
            assert rfile.get_absolute_url() in zipped_contents, zipped_contents
            assert "This file was redacted by" in zipped_contents, zipped_contents


def test_create_release_new_style_reupload():
    rfile = ReleaseFileFactory(name="file1.txt", filehash="hash")

    files = [
        {
            "name": "file1.txt",
            "path": "path/to/file1.txt",
            "url": "",
            "size": 4,
            "sha256": "hash",
            "mtime": "2022-08-17T13:37Z",
            "metadata": {},
        }
    ]

    with pytest.raises(releases.ReleaseFileAlreadyExists):
        releases.create_release(
            rfile.release.workspace,
            rfile.release.backend,
            rfile.release.created_by,
            files,
        )


def test_create_release_new_style_success():
    backend = BackendFactory()
    workspace = WorkspaceFactory()
    user = UserFactory()
    files = [
        {
            "name": "file1.txt",
            "path": "path/to/file1.txt",
            "url": "",
            "size": 7,
            "sha256": "hash",
            "date": "2022-08-17T13:37Z",
            "metadata": {},
        }
    ]

    release = releases.create_release(workspace, backend, user, files)

    assert release.requested_files == files
    assert release.files.count() == 1

    rfile = release.files.first()
    rfile.filehash == "hash"
    rfile.size == 7


def test_create_release_success():
    backend = BackendFactory()
    workspace = WorkspaceFactory()
    user = UserFactory()
    files = {"file1.txt": "hash"}
    release = releases.create_release(workspace, backend, user, files)
    assert release.requested_files == files


def test_create_release_reupload():
    rfile = ReleaseFileFactory(name="file1.txt", filehash="hash")
    files = {"file1.txt": "hash"}
    with pytest.raises(releases.ReleaseFileAlreadyExists):
        releases.create_release(
            rfile.release.workspace,
            rfile.release.backend,
            rfile.release.created_by,
            files,
        )


def test_handle_release_upload_file_created(build_release, file_content):
    release = build_release(["file1.txt"])

    filehash = hashlib.sha256(file_content).hexdigest()
    stream = io.BytesIO(file_content)

    rfile = releases.handle_file_upload(
        release,
        release.backend,
        release.created_by,
        stream,
        "file1.txt",
    )
    assert rfile.name == "file1.txt"
    assert rfile.path == f"{release.workspace.name}/releases/{release.id}/file1.txt"
    assert rfile.filehash == filehash


def test_handle_release_upload_exists_in_db_and_not_on_disk(file_content):
    filehash = hashlib.sha256(file_content).hexdigest()
    stream = io.BytesIO(file_content)

    existing = ReleaseFileFactory(
        name="file1.txt",
        path="foo/file1.txt",
        filehash=filehash,
        uploaded_at=None,
    )

    # check out test setup is correct
    assert existing.filehash == filehash

    # upload same files
    releases.handle_file_upload(
        existing.release,
        existing.release.backend,
        existing.created_by,
        stream,
        "file1.txt",
    )

    existing.refresh_from_db()

    assert existing.uploaded_at
    assert existing.absolute_path().exists()


def test_handle_release_upload_exists_in_db_and_on_disk(release):
    existing = release.files.first()
    stream = io.BytesIO(existing.absolute_path().read_bytes())

    # upload same files
    with pytest.raises(releases.ReleaseFileAlreadyExists):
        releases.handle_file_upload(
            existing.release,
            existing.release.backend,
            existing.created_by,
            stream,
            existing.name,
        )


def test_handle_release_upload_exists_with_incorrect_filehash(file_content):
    stream = io.BytesIO(file_content)

    existing = ReleaseFileFactory(
        name="file1.txt",
        path="foo/file1.txt",
        filehash="hash",
        uploaded_at=None,
    )

    with pytest.raises(Exception, match="^Contents of uploaded"):
        releases.handle_file_upload(
            existing.release,
            existing.release.backend,
            existing.created_by,
            stream,
            "file1.txt",
        )


def test_handle_release_upload_db_error(monkeypatch, build_release):
    release = build_release(["file1.txt"])

    monkeypatch.setattr(ReleaseFile.objects, "create", raise_error)
    with pytest.raises(DatabaseError):
        releases.handle_file_upload(
            release,
            release.backend,
            release.created_by,
            io.BytesIO(b"test"),
            "file1.txt",
        )

    # check the file has been deleted due to the error
    rpath = f"{release.workspace.name}/releases/{release.id}/file1.txt"
    assert not absolute_file_path(rpath).exists()


def test_serve_file(rf):
    # FIXME: we only serve a file if it's found.  While testing the
    # multi-select/review flow in the SPA we removed the only path which called
    # serve_file with a deleted file to have it redirect to release-hatch.  We
    # might not keep that path in so we're not removing this guard from
    # serve_file(), but we still want to maintain coverage.
    rfile = ReleaseFile(deleted_at=timezone.now(), deleted_by=UserFactory())
    request = rf.get("/")

    with pytest.raises(NotFound):
        releases.serve_file(request, rfile)


def test_workspace_files_no_releases():
    workspace = WorkspaceFactory()

    assert releases.workspace_files(workspace) == {}


def test_workspace_files_one_release(build_release):
    backend = BackendFactory(slug="backend")
    names = ["test1", "test2", "test3"]
    release = build_release(names, backend=backend)
    for name in names:
        ReleaseFileFactory(
            release=release,
            workspace=release.workspace,
            name=name,
        )

    output = releases.workspace_files(release.workspace)

    assert output == {
        "backend/test1": release.files.get(name="test1"),
        "backend/test2": release.files.get(name="test2"),
        "backend/test3": release.files.get(name="test3"),
    }


def test_workspace_files_many_releases(time_machine, build_release_with_files):
    now = timezone.now()

    backend1 = BackendFactory(slug="backend1")
    backend2 = BackendFactory(slug="backend2")
    workspace = WorkspaceFactory()

    build_release_with_files(
        ["test1", "test2", "test3"],
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 10),
    )
    build_release_with_files(
        ["test2", "test3"],
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 8),
    )
    release3 = build_release_with_files(
        ["test2"],
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 6),
    )
    release4 = build_release_with_files(
        ["test1", "test3"],
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 4),
    )
    release5 = build_release_with_files(
        ["test1"],
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 2),
    )
    # different backend, same file name, more recent
    release6 = build_release_with_files(
        ["test1"],
        workspace=workspace,
        backend=backend2,
        created_at=minutes_ago(now, 1),
    )

    output = releases.workspace_files(workspace)

    assert output == {
        "backend1/test1": release5.files.get(name="test1"),
        "backend1/test3": release4.files.get(name="test3"),
        "backend1/test2": release3.files.get(name="test2"),
        "backend2/test1": release6.files.get(name="test1"),
    }
