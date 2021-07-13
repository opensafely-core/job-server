import hashlib
import io
import json
import os
import shutil
from zipfile import ZipFile

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Release, ReleaseFile


MANIFEST_PATH = "metadata/manifest.json"


@transaction.atomic
def handle_release(workspace, backend, backend_user, release_hash, upload):
    try:
        # check for duplicates
        existing_release = Release.objects.get(id=release_hash)
        return existing_release, False
    except Release.DoesNotExist:
        pass

    # Even though IDs are globally unique, we partition the filesystem
    # structure into workspace directories, for 2 reasons:
    # 1. avoid dumping everything in one big directory.
    # 2. much easier for human operators to navigate on disk (e.g. for removal
    #    of any disclosive information).
    upload_dir = os.path.join(workspace.name, "releases", release_hash)
    actual_dir = None

    try:
        # first, ensure we can extract the zip
        with ZipFile(upload) as archive:
            try:
                json.load(archive.open(MANIFEST_PATH))
            except KeyError:
                raise ValidationError(
                    {"detail": "metadata/manifest.json file not found in zip"}
                )
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    {"detail": f"metadata/manifest.json file is not valid json: {exc}"}
                )

            actual_dir = extract_upload(upload_dir, archive)

        calculated_hash, files = hash_files(actual_dir)
        if calculated_hash != release_hash:
            raise ValidationError(
                {
                    "detail": f"provided hash {release_hash} did not match files hash of {calculated_hash}"
                }
            )

        release = Release.objects.create(
            id=release_hash,
            workspace=workspace,
            backend=backend,
            backend_user=backend_user,
            upload_dir=upload_dir,
        )
        for name in files:
            ReleaseFile.objects.create(
                workspace=workspace,
                release=release,
                name=name,
                path=os.path.join(upload_dir, name),
            )

    except Exception:
        # something went wrong, clean up files, they will need to reupload
        shutil.rmtree(actual_dir, ignore_errors=True)
        raise

    return release, True


def hash_files(directory):
    """Sort files in the directory and the hash them in that order."""
    relative_paths = (
        p.relative_to(directory) for p in directory.glob("**/*") if p.is_file()
    )
    files = list(sorted(f for f in relative_paths if str(f) != MANIFEST_PATH))
    # use md5 because its fast, and we only care about uniqueness, not security
    hash = hashlib.md5()  # noqa: A001
    for filename in files:
        path = directory / filename
        assert path.is_file(), f"{path} is not a file"
        hash.update(path.read_bytes())
    return hash.hexdigest(), files


def extract_upload(upload_dir, archive):
    actual_dir = settings.RELEASE_STORAGE / upload_dir
    actual_dir.parent.mkdir(exist_ok=True, parents=True)
    archive.extractall(actual_dir)
    return actual_dir


DEFAULT_MANIFEST = object()


def create_upload_zip(directory, manifest=DEFAULT_MANIFEST):
    """Create a zipfile stream from a directory of files.

    If there is no metadata/manifest.json in the directory, it will create
    a default dummy one. If you passmanifest=None, it will not generate
    a manifest.

    Mainly used in testing and development.
    """
    zipstream = io.BytesIO()
    manifest_data = None
    hash, files = hash_files(directory)  # noqa: A001

    manifest_path = directory / MANIFEST_PATH
    if manifest_path.exists():
        manifest_data = manifest_path.read_text()
    elif manifest is DEFAULT_MANIFEST:
        manifest_data = json.dumps(
            {
                "workspace": "workspace",
                "repo": "repo",
            }
        )
    elif manifest is not None:
        # no tests using this yet, hence the no cover. But they will
        manifest_data = json.dumps(manifest)  # pragma: no cover

    with ZipFile(zipstream, "w") as zf:
        for filename in files:
            zf.write(directory / filename, arcname=str(filename))
        if manifest_data:
            zf.writestr(MANIFEST_PATH, manifest_data)

    zipstream.seek(0)
    return hash, zipstream


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
