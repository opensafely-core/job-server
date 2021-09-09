from django.db import transaction
from django.utils import timezone


def release_file_delete(rfile, user):
    """Delete a release file"""

    with transaction.atomic():
        # delete file on disk
        rfile.absolute_path().unlink()

        rfile.deleted_by = user
        rfile.deleted_at = timezone.now()
        rfile.save()
