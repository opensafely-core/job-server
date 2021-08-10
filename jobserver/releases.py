import hashlib
import io
import zipfile
from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from furl import furl

from .models import Release, ReleaseFile
from .models.outputs import absolute_file_path
from .signing import AuthToken


class ReleaseFileAlreadyExists(Exception):
    pass


def build_hatch_token_and_url(*, backend, workspace, user, expiry=None):
    """Build an auth token and base URL for talking to release hatch"""
    # build the base URL for which we want the auth token to authenticate,
    # all paths beneath this one will be valid with the token
    f = furl(backend.level_4_url)
    f.path.segments += ["workspace", workspace.name]

    if expiry is None:
        expiry = timezone.now() + timedelta(minutes=30)

    builder = AuthToken(
        url=f.url,
        user=user.username,
        expiry=expiry,
    )
    token = builder.sign(key=backend.auth_token, salt="hatch")

    return token, f.url


def build_outputs_zip(release_files):
    # create an in memory stream so we don't need to write the file to disk
    in_memory_zf = io.BytesIO()

    # add each ReleaseFile to the zip using their name as the name in the
    # archive
    with zipfile.ZipFile(in_memory_zf, "w") as zip_obj:
        for rfile in release_files:
            zip_obj.write(rfile.absolute_path(), arcname=rfile.name)

    # rewind the file stream to the start
    in_memory_zf.seek(0)

    return in_memory_zf


def build_spa_base_url(full_path, file_path):
    """
    Break the full path of a page down into the URL path without any file path

    Given a URL such as

        /org/project/workspace/releases/string/path/to/file.csv

    we want to tell the SPA about the page path

        /org/project/workspace/releases/string/

    """
    return full_path.removesuffix(file_path)


def check_not_already_uploaded(filename, filehash, backend):
    """Check if this filename/filehash combination has been uploaded before."""
    duplicate = ReleaseFile.objects.filter(
        release__backend=backend,
        name=filename,
        filehash=filehash,
    )
    if duplicate.exists():
        raise ReleaseFileAlreadyExists(
            f"This version of '{filename}' has already been uploaded from backend '{backend.name}'"
        )


@transaction.atomic
def create_release(workspace, backend, created_by, requested_files, **kwargs):

    for filename, filehash in requested_files.items():
        check_not_already_uploaded(filename, filehash, backend)

    release = Release.objects.create(
        workspace=workspace,
        backend=backend,
        created_by=created_by,
        requested_files=requested_files,
        **kwargs,
    )
    return release


@transaction.atomic
def handle_file_upload(release, backend, user, upload, filename):
    """Validate and save an uploaded file to disk and database.

    Does basic detection of re-uploads of the same file, to avoid duplication.
    """
    # This reads the whole file into memory, but should not be a problem.
    # TODO: enforce a max upload size?
    data = upload.read()
    calculated_hash = hashlib.sha256(data).hexdigest()
    check_not_already_uploaded(filename, calculated_hash, backend)

    # We group the directory structure by workspace for 2 reasons:
    # 1. avoid dumping everything in one big directory.
    # 2. much easier for human operators to navigate on disk if needed.
    relative_path = (
        Path(release.workspace.name) / "releases" / str(release.id) / filename
    )
    absolute_path = absolute_file_path(relative_path)
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(data)

    try:
        rfile = ReleaseFile.objects.create(
            release=release,
            workspace=release.workspace,
            created_by=user,
            name=filename,
            path=str(relative_path),
            filehash=calculated_hash,
        )
    except Exception:
        # something went wrong, clean up file, they will need to reupload
        absolute_path.unlink(missing_ok=True)
        raise

    return rfile


def workspace_files(workspace):
    """
    Gets the latest version of each file for each backend in this Workspace.

    Returns a mapping of the workspace-relative file name (which includes
    backend) to its RequestFile model.

    We use Python to find the latest version of each file because SQLite
    doesn't support DISTINCT ON so we can't use
    `.distinct("release__created_at")`.
    """
    index = {}
    for rfile in workspace.files.order_by("-release__created_at"):
        workspace_path = f"{rfile.release.backend.name}/{rfile.name}"
        if workspace_path not in index:
            index[workspace_path] = rfile
    return index
