from datetime import datetime
import hashlib
import os
import shutil
from zipfile import ZipFile

from django.db import transaction
from django.conf import settings

from .models import Release


@transaction.atomic
def handle_release(workspace, backend, backend_user, release_hash, upload):
    try:
        # check for duplicates
        existing_release = Release.objects.get(id=release_hash)
        return existing_release, False
    except Release.DoesNotExist:
        pass

    # Even though id's are globally unique, we partition the filesystem
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
            archive.extractall(actual_dir)

        calculated_hash = hash_files(actual_dir)
        if calculated_hash != release_hash:
            raise Exception(f"provided hash {release_hash} did not match files hash of {calculated_hash}")

        release = Release.objects.create(
            id=release_hash,
            workspace=workspace,
            backend=backend,
            backend_user=backend_user,
            upload_dir=upload_dir,
            files=os.listdir(actual_dir),
        )

    except Exception:
        # something went wrong, clean up files, they will need to reupload
        shutil.rmtree(actual_dir, ignore_errors=True)
        raise

    # TODO: push zip to Github as release.

    return release, True


def hash_files(directory):
    # use md5 because its fast, and we only care about uniqueness, not security
    hash = hashlib.md5()
    for filename in sorted(directory.glob('**/*')):
        if filename.is_file():
            hash.update(filename.read_bytes())
    return hash.hexdigest()

