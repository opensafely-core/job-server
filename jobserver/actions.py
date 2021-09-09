from django.db import transaction
from django.utils import timezone

from .authorization.utils import require_permission


@require_permission("release_file_delete", "project")
def release_file_delete(*, user, rfile, project):
    """Delete a release file"""

    with transaction.atomic():
        # delete file on disk
        rfile.absolute_path().unlink()

        rfile.deleted_by = user
        rfile.deleted_at = timezone.now()
        rfile.save()
