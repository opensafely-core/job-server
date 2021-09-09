from django.db import transaction
from django.utils import timezone

from .authorization import roles
from .authorization.utils import require_role


@require_role(roles.OutputChecker, "project")
def release_file_delete(*, user, rfile, project):
    """Delete a release file"""
    with transaction.atomic():
        # delete file on disk
        rfile.absolute_path().unlink()

        rfile.deleted_by = user
        rfile.deleted_at = timezone.now()
        rfile.save()
