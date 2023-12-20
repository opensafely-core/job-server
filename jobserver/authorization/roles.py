from .permissions import (
    analysis_request_create,
    analysis_request_view,
    application_manage,
    backend_manage,
    job_cancel,
    job_run,
    org_create,
    release_file_delete,
    release_file_upload,
    release_file_view,
    repo_sign_off_with_outputs,
    snapshot_create,
    snapshot_publish,
    unreleased_outputs_view,
    user_manage,
    workspace_archive,
    workspace_create,
    workspace_toggle_notifications,
)


class CoreDeveloper:
    """
    Bennett staff member with administrator access to Job Server.

    Note the name is misleading here as this does not imply what we generally mean by
    "core developer". We plan to rename this role as part of a more general permissions
    revamp.
    """

    display_name = "Core Developer"
    description = (
        "Bennett staff member with administrator access to Job Server. "
        "(Not necessarily a developer – this role will be renamed eventually.)"
    )
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        application_manage,
        backend_manage,
        org_create,
        user_manage,
    ]


class InteractiveReporter:
    """Use the interactive UI"""

    display_name = "Interactive Reporter"
    description = ""
    models = [
        "jobserver.models.core.ProjectMembership",
        "jobserver.models.core.User",
    ]
    permissions = [
        analysis_request_create,
        analysis_request_view,
        release_file_view,
    ]


class OrgCoordinator:
    """
    A responsible party for an Org
    """

    display_name = "Organisation Coordinator"
    description = ""
    models = [
        "jobserver.models.core.OrgMembership",
    ]
    permissions = []


class OutputChecker:
    """
    Review output folders that have been proposed for release.
    """

    display_name = "Output Checker"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        release_file_delete,
        release_file_upload,
        unreleased_outputs_view,
    ]


class OutputPublisher:
    """
    Release approved-only outputs to a public location based on the work of the
    output checkers and/or an OpenSAFELY Reviewer.
    """

    display_name = "Output Publisher"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        snapshot_publish,
    ]


class ProjectCollaborator:
    """
    TODO: Define this role.
    """

    display_name = "Project Collaborator"
    description = "View unpublished outputs released from Level 4 to the Jobs site."
    models = [
        "jobserver.models.core.ProjectInvitation",
        "jobserver.models.core.ProjectMembership",
        "jobserver.models.core.User",
    ]
    permissions = [
        release_file_view,
    ]


class ProjectDeveloper:
    """
    An external user who is developing and executing code to analyse data in
    OpenSAFELY; they will likely want to review (and flag for release) their
    own outputs.
    """

    display_name = "Project Developer"
    description = (
        "Run and cancel Jobs, publish released outputs, and manage workspaces."
    )
    models = [
        "jobserver.models.core.ProjectInvitation",
        "jobserver.models.core.ProjectMembership",
        "jobserver.models.core.User",
    ]
    permissions = [
        job_cancel,
        job_run,
        snapshot_create,
        unreleased_outputs_view,
        workspace_archive,
        workspace_create,
        workspace_toggle_notifications,
    ]


class SignOffRepoWithOutputs:
    """Internally sign off repos with outputs hosted on GitHub"""

    display_name = "Sign Off Repos with Outputs"
    description = "Internally sign off repos with outputs hosted on GitHub"
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        repo_sign_off_with_outputs,
    ]
