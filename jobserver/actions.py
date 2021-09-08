from django.db import transaction
from django.utils import timezone

from .authorization import roles
from .authorization.utils import require_role


@transaction.atomic
@require_role(roles.OutputChecker, "project")
def delete_release_file(*, user, rfile, project):
    # delete file on disk
    rfile.absolute_path().unlink()

    rfile.deleted_by = user
    rfile.deleted_at = timezone.now()
    rfile.save()
