import random
import string
import zipfile
from datetime import timedelta

import pytest
from django.db import DatabaseError
from django.utils import timezone

from jobserver import releases
from jobserver.models import ReleaseFile
from jobserver.models.outputs import absolute_file_path
from tests.factories import (
    BackendFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    ReleaseUploadsFactory,
    UserFactory,
    WorkspaceFactory,
)

from ..utils import minutes_ago


def raise_error(**kwargs):
    raise DatabaseError("test error")


@pytest.mark.django_db
def test_build_hatch_token_and_url_default():
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    releases.build_hatch_token_and_url(
        backend=backend,
        workspace=workspace,
        user=user,
    )


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_build_outputs_zip():
    release = ReleaseFactory(ReleaseUploadsFactory(["test1"]))

    zf = releases.build_outputs_zip(release.files.all())

    with zipfile.ZipFile(zf, "r") as zip_obj:
        assert zip_obj.testzip() is None

        assert zip_obj.namelist() == ["test1"]

        with open(release.files.first().absolute_path(), "rb") as f:
            original_contents = f.read()

        with zip_obj.open("test1") as f:
            zipped_contents = f.read()

        # check the zipped files contents match the original files contents
        assert zipped_contents == original_contents


@pytest.mark.django_db
def test_create_release_success():
    backend = BackendFactory()
    workspace = WorkspaceFactory()
    user = UserFactory()
    files = {"file1.txt": "hash"}
    release = releases.create_release(workspace, backend, user, files)
    assert release.requested_files == files


@pytest.mark.django_db
def test_create_release_reupload():
    uploads = ReleaseUploadsFactory({"file1.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    files = {"file1.txt": rfile.filehash}
    with pytest.raises(releases.ReleaseFileAlreadyExists):
        releases.create_release(
            release.workspace, release.backend, release.created_by, files
        )


@pytest.mark.django_db
def test_handle_release_upload_file_created():
    uploads = ReleaseUploadsFactory({"file1.txt": b"test"})
    release = ReleaseFactory(uploads, uploaded=False)

    rfile = releases.handle_file_upload(
        release,
        release.backend,
        release.created_by,
        uploads[0].stream,
        uploads[0].filename,
    )
    assert rfile.name == "file1.txt"
    assert rfile.path == f"{release.workspace.name}/releases/{release.id}/file1.txt"
    assert rfile.filehash == uploads[0].filehash


@pytest.mark.django_db
def test_handle_release_upload_already_exists():
    uploads = ReleaseUploadsFactory({"file1.txt": b"test"})
    existing = ReleaseFileFactory(uploads[0])

    # check out test setup is correct
    assert existing.filehash == uploads[0].filehash

    # upload same files
    with pytest.raises(releases.ReleaseFileAlreadyExists):
        releases.handle_file_upload(
            existing.release,
            existing.release.backend,
            existing.created_by,
            uploads[0].stream,
            uploads[0].filename,
        )


@pytest.mark.django_db
def test_handle_release_upload_db_error(monkeypatch):
    uploads = ReleaseUploadsFactory({"file1.txt": b"test"})
    release = ReleaseFactory(uploads, uploaded=False)

    monkeypatch.setattr(ReleaseFile.objects, "create", raise_error)
    with pytest.raises(DatabaseError):
        releases.handle_file_upload(
            release,
            release.backend,
            release.created_by,
            uploads[0].stream,
            uploads[0].filename,
        )

    # check the file has been deleted due to the error
    rpath = f"{release.workspace.name}/releases/{release.id}/{uploads[0].filename}"
    assert not absolute_file_path(rpath).exists()


@pytest.mark.django_db
def test_workspace_files_no_releases():
    workspace = WorkspaceFactory()

    assert releases.workspace_files(workspace) == {}


@pytest.mark.django_db
def test_workspace_files_one_release():
    backend = BackendFactory(name="backend")
    uploads = ReleaseUploadsFactory(["test1", "test2", "test3"])
    release = ReleaseFactory(uploads, backend=backend)

    output = releases.workspace_files(release.workspace)

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

    def uploads(files):
        """Generate files with unique contents."""
        content = "".join(random.choice(string.ascii_letters) for i in range(10))
        return ReleaseUploadsFactory({f: content.encode("utf8") for f in files})

    ReleaseFactory(
        uploads(["test1", "test2", "test3"]),
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 10),
    )
    ReleaseFactory(
        uploads(["test2", "test3"]),
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 8),
    )
    release3 = ReleaseFactory(
        uploads(["test2"]),
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 6),
    )
    release4 = ReleaseFactory(
        uploads(["test1", "test3"]),
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 4),
    )
    release5 = ReleaseFactory(
        uploads(["test1"]),
        workspace=workspace,
        backend=backend1,
        created_at=minutes_ago(now, 2),
    )
    # different backend, same file name, more recent
    release6 = ReleaseFactory(
        uploads(["test1"]),
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
