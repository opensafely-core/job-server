from django.db import transaction
from django.utils import timezone

from . import releases
from .authorization import roles
from .authorization.utils import require_role


@transaction.atomic
@require_role(roles.OutputChecker, "project")
def release_file_delete(*, user, rfile, project):
    # delete file on disk
    rfile.absolute_path().unlink()

    rfile.deleted_by = user
    rfile.deleted_at = timezone.now()
    rfile.save()


@require_role(roles.ProjectCollaborator)
def release_file_view():
    pass


@require_role(roles.OutputChecker, "project")
def release_file_upload(*, user, release, backend, upload, filename, project):
    return releases.handle_file_upload(release, backend, user, upload, filename)


@require_role(roles.OutputChecker, "project")
def release_workspace_create(*, user, workspace, backend, files, project):
    return releases.create_release(workspace, backend, user, files)
