from django.db import transaction
from django.utils import timezone

from .authorization.utils import require_permission


@transaction.atomic
@require_permission("release_file_delete", "project")
def delete_release_file(*, user, rfile, project):
    # delete file on disk
    rfile.absolute_path().unlink()

    rfile.deleted_by = user
    rfile.deleted_at = timezone.now()
    rfile.save()
