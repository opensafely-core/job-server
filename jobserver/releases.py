import hashlib
import json
import os
import shutil
from zipfile import ZipFile

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Release


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
    upload_dir = os.path.join(workspace.name, release_hash)
    actual_dir = settings.RELEASE_STORAGE / upload_dir
    actual_dir.parent.mkdir(exist_ok=True, parents=True)

    try:
        # first, ensure we can extract the zip
        with ZipFile(upload) as archive:
            try:
                json.load(archive.open("metadata/manifest.json"))
            except KeyError:
                raise ValidationError(
                    {"detail": "metadata/manifest.json file not found in zip"}
                )
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    {"detail": f"metadata/manifest.json file is not valid json: {exc}"}
                )

            archive.extractall(actual_dir)

        files = list_files(actual_dir)
        calculated_hash = hash_files(actual_dir, files)
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
            files=[str(f) for f in files],
        )

    except Exception:
        # something went wrong, clean up files, they will need to reupload
        shutil.rmtree(actual_dir, ignore_errors=True)
        raise

    return release, True


def list_files(directory):
    """Utility to list files in a directory tree."""
    return list(
        sorted(p.relative_to(directory) for p in directory.glob("**/*") if p.is_file())
    )


def hash_files(directory, files):
    # use md5 because its fast, and we only care about uniqueness, not security
    hash = hashlib.md5()
    for filename in files:
        path = directory / filename
        assert path.is_file(), f"{path} is not a file"
        hash.update(path.read_bytes())
    return hash.hexdigest()
