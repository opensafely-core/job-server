from .permissions import (
    application_manage,
    backend_manage,
    job_cancel,
    job_run,
    org_create,
    project_invite_members,
    project_membership_edit,
    project_review,
    release_file_delete,
    release_file_upload,
    release_file_view,
    snapshot_create,
    snapshot_publish,
    user_manage,
    workspace_archive,
    workspace_create,
    workspace_toggle_notifications,
)


class CoreDeveloper:
    """
    Internal user who develops and deploys opensafely core framework code.
    """

    display_name = "Core Developer"
    description = (
        "Internal user who develops and deploys the OpenSAFELY core framework."
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


class DataInvestigator:
    """
    Has access to Level 2 pseudonymised data, typically over a SQL browser, to
    understand and debug raw underlying data. Sometimes a core developer, and
    in rare and exceptional cases, a study developer.  Typically DataLab staff
    only.
    """

    display_name = "Data Investigator"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = []


class GovernanceReviewer:
    """
    IG, COPI coverage, and ethics for each project by each team, currently this
    is performed by NHSE.
    """

    display_name = "Governance Reviewer"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = []


class OnboardingAgent:
    """
    A developer and/or developer-researcher from the OpenSAFELY team with deep
    knowledge of OpenSAFELY who is providing ongoing collaborative technical,
    data science, analysis and academic support to external users who are
    delivering a project, to a degree that has been pre-planned and resourced.
    """

    display_name = "Onboarding Agent"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = []


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


class ProjectCoordinator:
    """
    The responsible party for a Project

    They are responsible for:
     - all administrative and permissions aspects of the project
     - they are the single point of contact for the OpenSAFELY team
     - they may be the external study PI, or Study Developer.

    A Project can only have one Project Coordinator.
    """

    display_name = "Project Coordinator"
    description = "An administrator for the Project."
    models = [
        "jobserver.models.core.ProjectInvitation",
        "jobserver.models.core.ProjectMembership",
        "jobserver.models.core.User",
    ]
    permissions = [
        project_invite_members,
        project_membership_edit,
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
        workspace_archive,
        workspace_create,
        workspace_toggle_notifications,
    ]


class TechnicalReviewer:
    """
    Evaluation of the feasibility of the project and the skills of the
    applicants, by OpenSAFELY.
    """

    display_name = "Technical Reviewer"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        project_review,
    ]
