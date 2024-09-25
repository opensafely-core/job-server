from .permissions import (
    analysis_request_view,
    application_manage,
    backend_manage,
    job_cancel,
    job_run,
    org_create,
    project_manage,
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
    display_name = "Staff Area Administrator"
    description = """Access the Staff Area.
    View and edit applications, backends, organisations, project, repos, users, and workspaces.
    View dashboards.
    See Staff Area Administrator Log for the list of individuals who are approved for this role."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        application_manage,
        backend_manage,
        org_create,
        user_manage,
    ]


class InteractiveReporter:
    display_name = "Interactive Reporter"
    description = """View analysis requests and reports for projects that used OpenSAFELY Interactive."""
    models = [
        "jobserver.models.project_membership.ProjectMembership",
        "jobserver.models.user.User",
    ]
    permissions = [
        analysis_request_view,
        release_file_view,
    ]


class OutputChecker:
    display_name = "Output Checker"
    description = """View, upload, and delete any outputs that have been released to Job Server.
    View unreleased files on the Level 4 Server."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        release_file_delete,
        release_file_upload,
        release_file_view,
        unreleased_outputs_view,
    ]


class OutputPublisher:
    display_name = "Output Publisher"
    description = """Publish released outputs (i.e make visible to the public) as a result of a request by a Project Developer."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        snapshot_publish,
    ]


class ProjectCollaborator:
    display_name = "Project Collaborator"
    description = """View outputs that have been released to Job Server."""
    models = [
        "jobserver.models.project_membership.ProjectMembership",
        "jobserver.models.user.User",
    ]
    permissions = [
        release_file_view,
    ]


class ProjectDeveloper:
    display_name = "Project Developer"
    description = """Run and cancel jobs.
    Edit project status and description.
    Create and manage workspaces.
    View unreleased outputs on Level 4 and request their release.
    Request that released outputs are published."""
    models = [
        "jobserver.models.project_membership.ProjectMembership",
    ]
    permissions = [
        job_cancel,
        job_run,
        project_manage,
        release_file_view,
        snapshot_create,
        unreleased_outputs_view,
        workspace_archive,
        workspace_create,
        workspace_toggle_notifications,
    ]


class SignOffRepoWithOutputs:
    display_name = "Sign Off Repos with Outputs"
    description = """Internally sign off repos with outputs hosted on GitHub."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        repo_sign_off_with_outputs,
    ]


class DeploymentAdministrator:
    display_name = "Deployment Administrator"
    description = """Run and cancel jobs on any project, for development and maintenance purposes, including technical support for Approved Projects.
    See Developer Permissions Log for the list of individuals who are approved for this role.
    """
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        job_cancel,
        job_run,
    ]
