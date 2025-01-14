import hashlib
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from django.utils.http import http_date
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Release, ReleaseFile
from .models.release_file import absolute_file_path


class ReleaseFileAlreadyExists(Exception):
    pass


class ReleaseFileHashMismatch(Exception):
    pass


def _build_paths(release, filename, data):
    """
    Build the absolute path for a given filename as part of a release

    We group the directory structure by workspace for 2 reasons:
    1. avoid dumping everything in one big directory.
    2. much easier for human operators to navigate on disk if needed.
    """
    relative_path = (
        Path(release.workspace.name) / "releases" / str(release.id) / filename
    )
    absolute_path = absolute_file_path(relative_path)
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    return relative_path, absolute_path


def build_outputs_zip(release_files, url_builder_func):
    # create an in memory stream so we don't need to write the file to disk
    in_memory_zf = io.BytesIO()

    # add each ReleaseFile to the zip using their name as the name in the
    # archive
    with zipfile.ZipFile(in_memory_zf, "w") as zip_obj:
        for rfile in release_files:
            if not rfile.is_deleted:
                zip_obj.write(rfile.absolute_path(), arcname=rfile.name)
                continue

            # explain why an on-disk file was deleted, and potentially
            # overwrite the previously unredacted version.
            name = rfile.deleted_by.name if rfile.deleted_by else "Unknown"
            deleted_at = rfile.deleted_at if rfile.deleted_at else "Unknown"
            first_line = f"This file was redacted by {name} on {deleted_at}"

            url = url_builder_func(rfile.get_absolute_url())
            second_line = f"For more information see: {url}"

            zip_obj.writestr(rfile.name, f"{first_line}\n\n{second_line}")

    # rewind the file stream to the start
    in_memory_zf.seek(0)

    return in_memory_zf


def check_not_already_uploaded(workspace, filename, filehash, backend):
    """Check if this workspace/filename/filehash combination has been uploaded before."""
    duplicate = ReleaseFile.objects.filter(
        release__backend=backend,
        workspace=workspace,
        name=filename,
        filehash=filehash,
    )
    if duplicate.exists():
        raise ReleaseFileAlreadyExists(
            f"This version of '{filename}' in workspace {workspace} has already been uploaded from backend '{backend.slug}'"
        )


@transaction.atomic
def create_release(workspace, backend, created_by, requested_files, **kwargs):
    for f in requested_files:
        check_not_already_uploaded(workspace, f["name"], f["sha256"], backend)

    release = Release.objects.create(
        workspace=workspace,
        backend=backend,
        created_by=created_by,
        requested_files=requested_files,
        **kwargs,
    )

    for f in requested_files:
        ReleaseFile.objects.create(
            release=release,
            workspace=release.workspace,
            created_by=created_by,
            name=f["name"],
            filehash=f["sha256"],
            size=f["size"],
            mtime=f["date"],
            metadata=f["metadata"],
        )

    return release


@transaction.atomic
def handle_file_upload(release, backend, user, upload, filename, **kwargs):
    """Validate and save an uploaded file to disk and database.

    Does basic detection of re-uploads of the same file, to avoid duplication.
    """
    # This reads the whole file into memory, but should not be a problem.
    # TODO: enforce a max upload size?
    data = upload.read()
    calculated_hash = hashlib.sha256(data).hexdigest()
    relative_path, absolute_path = _build_paths(release, filename, data)

    # Check if this filename for this release has been uploaded before.
    rfile = ReleaseFile.objects.filter(
        release=release,
        release__backend=backend,
        name=filename,
    ).first()

    if not rfile:  # old flow
        absolute_path.write_bytes(data)

        mtime = datetime.fromtimestamp(absolute_path.stat().st_mtime, tz=UTC)
        size = absolute_path.stat().st_size

        try:
            return ReleaseFile.objects.create(
                release=release,
                workspace=release.workspace,
                created_by=user,
                uploaded_at=timezone.now(),
                name=filename,
                path=str(relative_path),
                filehash=calculated_hash,
                mtime=mtime,
                size=size,
                **kwargs,
            )
        except Exception:
            # something went wrong, clean up file, they will need to reupload
            absolute_path.unlink(missing_ok=True)
            raise

    # New flow

    # _is_ on disk
    if rfile.uploaded_at:
        # existence of a ReleaseFile isn't an error case now but a file-on-disk
        # having already been uploaded is
        raise ReleaseFileAlreadyExists(
            f"This version of '{filename}' has already been uploaded from backend '{backend.slug}'"
        )

    # We have a ReleaseFile but no file-on-disk, but we still need to confirm
    # the uploaded files hash matches what was sent to us when the ReleaseFile
    # and Release were created.
    if rfile.filehash != calculated_hash:
        msg = "Contents of uploaded file does not match the file which a review was requested for"
        raise ReleaseFileHashMismatch(msg)

    absolute_path.write_bytes(data)
    rfile.path = str(relative_path)
    rfile.uploaded_at = timezone.now()
    rfile.save(update_fields=["path", "uploaded_at"])

    return rfile


def serve_file(request, rfile):
    """Serve a ReleaseFile as the response.

    If Releases-Redirect header is set, use nginx's X-Accel-Redirect to serve
    response. Else just serve the bytes directly (for dev).
    """
    # check the file has been uploaded
    if rfile.is_deleted:
        raise NotFound

    if rfile.uploaded_at is None:
        return Response("File not yet uploaded")

    path = rfile.absolute_path()

    internal_redirect = request.headers.get("Releases-Redirect")
    if internal_redirect:
        # we're behind nginx, so use X-Accel-Redirect to serve the file
        # from nginx, relative to RELEASES_STORAGE.
        response = Response()
        response.headers["X-Accel-Redirect"] = f"{internal_redirect}/{rfile.path}"
    else:
        # serve directly from django in dev use regular django response to
        # bypass DRFs renderer framework and just serve bytes
        response = FileResponse(path.open("rb"))

        content_type = response.headers.get("Content-Type")
        if content_type.startswith("text"):
            # for text-based files append a charset to the existing
            # content-type header, being careful just in case the existing
            # value is empty
            joiner = "; " if content_type else ""
            response.headers["Content-Type"] = f"{content_type}{joiner}charset=utf-8"

    # set Last-Modified header as per:
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified
    response.headers["Last-Modified"] = http_date(rfile.created_at.timestamp())

    return response


def workspace_files(workspace):
    """
    Gets the latest version of each file for each backend in this Workspace.

    Returns a mapping of the workspace-relative file name (which includes
    backend) to its RequestFile model.
    """

    files = (
        workspace.files.select_related("release", "release__backend")
        .order_by("name", "-release__created_at")
        .distinct("name", "release__created_at")
    )
    index = {}
    for rfile in files:
        workspace_path = f"{rfile.release.backend.slug}/{rfile.name}"
        if workspace_path not in index:
            index[workspace_path] = rfile
    return index
