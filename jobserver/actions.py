from django.db import transaction
from django.utils import timezone

from . import releases
from .authorization import roles
from .authorization.utils import require_role


@require_role(roles.ProjectCoordinator, "project")
def cancel_project_invite(*, user, invite, project):
    """Cancel an existing Project invitation"""
    invite.delete()


@require_role(roles.OutputChecker, "project")
def delete_release_file(*, user, rfile, project):
    """Delete a release file"""
    with transaction.atomic():
        # delete file on disk
        rfile.absolute_path().unlink()

        rfile.deleted_by = user
        rfile.deleted_at = timezone.now()
        rfile.save()


@require_role(roles.ProjectCollaborator)
def view_release_file():
    """View a release file"""


@require_role(roles.OutputChecker, "project")
def upload_release_file(*, user, release, backend, upload, filename, project):
    """Upload a released file"""
    return releases.handle_file_upload(release, backend, user, upload, filename)


@require_role(roles.OutputChecker, "project")
def create_workspace_release(*, user, workspace, backend, files, project):
    """Create a release in a workspace"""
    return releases.create_release(workspace, backend, user, files)
