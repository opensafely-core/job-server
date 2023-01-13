from .permissions import (
    analysis_request_create,
    analysis_request_view,
    application_manage,
    backend_manage,
    job_cancel,
    job_request_pick_ref,
    job_run,
    org_create,
    project_review,
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
    in rare and exceptional cases, a study developer.  Typically Bennett
    Institute staff only.
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
    ]


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


class OpensafelyInteractive:
    """Use OSI specific parts of the site during the MVP"""

    display_name = "OpenSAFELY Interactive"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = [
        job_request_pick_ref,
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
