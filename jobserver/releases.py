import hashlib
import io
import textwrap
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from django.utils.http import http_date
from furl import furl
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from .models import Release, ReleaseFile
from .models.outputs import absolute_file_path
from .signing import AuthToken


class ReleaseFileAlreadyExists(Exception):
    pass


class ReleaseFileHashMismatch(Exception):
    pass


def size_formatter(value):
    """
    Format the value, in bytes, with a size suffix

    Kilobytes (Kb) and Megabytes (Mb) will be automatically selected if the
    values is large enough.
    """
    if value < 1024:
        return f"{value}b"

    if value < 1024**2:
        value = round(value / 1024, 2)
        return f"{value}Kb"

    value = round(value / 1024**2, 2)
    return f"{value}Mb"


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


def check_not_already_uploaded(filename, filehash, backend):
    """Check if this filename/filehash combination has been uploaded before."""
    duplicate = ReleaseFile.objects.filter(
        release__backend=backend,
        name=filename,
        filehash=filehash,
    )
    if duplicate.exists():
        raise ReleaseFileAlreadyExists(
            f"This version of '{filename}' has already been uploaded from backend '{backend.slug}'"
        )


@transaction.atomic
def create_release(workspace, backend, created_by, requested_files, **kwargs):
    # we infer a new style payload from it being a dict or list.  Once the new
    # style release UI is completed and in use, we can remove the old way of
    # doing things from here.
    new_style = isinstance(requested_files, list)

    if new_style:
        for f in requested_files:
            check_not_already_uploaded(f["name"], f["sha256"], backend)
    else:
        for filename, filehash in requested_files.items():
            check_not_already_uploaded(filename, filehash, backend)

    release = Release.objects.create(
        workspace=workspace,
        backend=backend,
        created_by=created_by,
        requested_files=requested_files,
        **kwargs,
    )

    if new_style:
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


def create_github_issue(
    release, github_api, org="ebmdatalab", repo="opensafely-output-review"
):
    template = """
    Requested by: {requested_by}
    Release: {release}
    GitHub repo: {github_repo}
    Workspace: {workspace}

    {number} files have been selected for review, with a total size of {size}.{review_form}

    **When you start a review please react to this message with :eyes:. When you have completed your review add a :thumbsup:. Once two reviews have been completed and a response has been sent to the requester, please close the issue.**
    """

    is_internal = release.created_by.orgs.filter(slug="datalab").exists()

    base_url = furl(settings.BASE_URL)

    def link(title, url):
        return f"[{title}]({url})"

    github_repo = link(release.workspace.repo.name, release.workspace.repo.url)
    requested_by = link(release.created_by.name, release.created_by.get_staff_url())
    release_url = link(release.id, base_url / release.get_absolute_url())
    workspace_url = link(
        release.workspace.name, base_url / release.workspace.get_absolute_url()
    )

    files = release.files.all()
    number = len(files)
    size = size_formatter(sum(f.size for f in files))
    review_form = "" if is_internal else "\n\n[Review request form]()"

    content = textwrap.dedent(template).format(
        github_repo=github_repo,
        number=number,
        release=release_url,
        requested_by=requested_by,
        review_form=review_form,
        size=size,
        workspace=workspace_url,
    )

    github_api.create_issue(
        org,
        repo,
        title=release.workspace.name,
        body=content,
        labels=["internal" if is_internal else "external"],
    )


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
        # file has not been uploaded yet
        # use release-hatch to view it, will only work if on level 4
        release = rfile.release
        auth_token, url = build_hatch_token_and_url(
            backend=release.backend,
            workspace=release.workspace,
            user=request.user,
        )
        # Note: because we need to add auth_token, we can't use a straight
        # redirect here. So we create an empty response and the js code
        # manually redirects. We may be able to do proper redirects in future
        # with a bit of work.
        response = Response(status=200)
        response.headers["Location"] = url + f"/release/{release.id}/{rfile.name}"
        response.headers["Authorization"] = auth_token
        return response

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
