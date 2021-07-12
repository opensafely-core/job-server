import hashlib
from pathlib import Path

from django.db import transaction

from .models import Release, ReleaseFile
from .models.outputs import absolute_file_path


@transaction.atomic
def create_release(workspace, backend, created_by, requested_files, **kwargs):
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

    # idempotency
    try:
        # check for duplicates
        # - same backend
        # - same filename
        # - same contents
        existing = ReleaseFile.objects.filter(
            release__backend=backend,
            name=filename,
            filehash=calculated_hash,
        ).get()
        return existing
    except ReleaseFile.DoesNotExist:
        pass

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
