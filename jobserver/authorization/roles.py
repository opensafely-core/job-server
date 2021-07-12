from .permissions import (
    cancel_job,
    check_output,
    create_org,
    invite_project_members,
    manage_backends,
    manage_project_members,
    manage_project_workspaces,
    manage_users,
    publish_output,
    review_project,
    run_job,
    view_release_file,
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
        cancel_job,
        create_org,
        invite_project_members,
        manage_backends,
        manage_project_members,
        manage_project_workspaces,
        manage_users,
        run_job,
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
        check_output,
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
        publish_output,
    ]


class ProjectCollaborator:
    """
    TODO: Define this role.
    """

    display_name = "Project Collaborator"
    description = ""
    models = [
        "jobserver.models.core.ProjectInvitation",
        "jobserver.models.core.ProjectMembership",
        "jobserver.models.core.User",
    ]
    permissions = [
        view_release_file,
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
        invite_project_members,
        manage_project_members,
        manage_project_workspaces,
    ]


class ProjectDeveloper:
    """
    An external user who is developing and executing code to analyse data in
    OpenSAFELY; they will likely want to review (and flag for release) their
    own outputs.
    """

    display_name = "Project Developer"
    description = "An external user who is developing and executing code to analyse data in OpenSAFELY; they will likely want to review (and flag for release) their own outputs."
    models = [
        "jobserver.models.core.ProjectInvitation",
        "jobserver.models.core.ProjectMembership",
    ]
    permissions = [
        cancel_job,
        check_output,
        run_job,
    ]


class SuperUser:
    """
    Full access to the OpenSAFELY platform.

    This is an interim Role to facilitate moving away from User.is_superuser
    checks.
    """

    display_name = "Super User"
    description = ""
    models = [
        "jobserver.models.core.User",
    ]
    permissions = []


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
        review_project,
    ]
