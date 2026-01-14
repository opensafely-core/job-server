from .permissions import Permission


class StaffAreaAdministrator:
    display_name = "Staff Area Administrator"
    description = """Access the Staff Area.
    View and edit applications, backends, organisations, project, repos, users, and workspaces.
    View dashboards.
    See Staff Area Administrator Log for the list of individuals who are approved for this role."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.APPLICATION_MANAGE,
        Permission.BACKEND_MANAGE,
        Permission.ORG_CREATE,
        Permission.USER_MANAGE,
        Permission.STAFF_AREA_ACCESS,
        Permission.USER_EDIT_PROJECT_ROLES,
    ]


class ServiceAdministrator:
    display_name = "Service Administrator"
    description = """DO NOT ASSIGN IN PRODUCTION.
    Access the Create Project page.
    Create projects.
    Assign users to projects and project roles."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.USER_EDIT_PROJECT_ROLES,
    ]


class OutputChecker:
    display_name = "Output Checker"
    description = """View, upload, and delete any outputs that have been released to Job Server.
    View unreleased outputs on Level 4 and release them to Job Server."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.RELEASE_FILE_DELETE,
        Permission.RELEASE_FILE_UPLOAD,
        Permission.RELEASE_FILE_VIEW,
        Permission.UNRELEASED_OUTPUTS_VIEW,
    ]


class OutputPublisher:
    display_name = "Output Publisher"
    description = """Publish released outputs (i.e make visible to the public) as a result of a request by a Project Developer."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.SNAPSHOT_PUBLISH,
    ]


class ProjectCollaborator:
    display_name = "Project Collaborator"
    description = """View outputs that have been released to Job Server."""
    models = [
        "jobserver.models.project_membership.ProjectMembership",
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.RELEASE_FILE_VIEW,
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
        Permission.JOB_CANCEL,
        Permission.JOB_RUN,
        Permission.PROJECT_MANAGE,
        Permission.RELEASE_FILE_VIEW,
        Permission.SNAPSHOT_CREATE,
        Permission.UNRELEASED_OUTPUTS_VIEW,
        Permission.WORKSPACE_ARCHIVE,
        Permission.WORKSPACE_CREATE,
        Permission.WORKSPACE_TOGGLE_NOTIFICATIONS,
    ]


class SignOffRepoWithOutputs:
    display_name = "Sign Off Repos with Outputs"
    description = """Internally sign off repos with outputs hosted on GitHub."""
    models = [
        "jobserver.models.user.User",
    ]
    permissions = [
        Permission.REPO_SIGN_OFF_WITH_OUTPUTS,
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
        Permission.JOB_CANCEL,
        Permission.JOB_RUN,
    ]
