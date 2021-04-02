from .permissions import (
    cancel_job,
    check_output,
    invite_project_members,
    publish_output,
    review_project,
    run_job,
)


class CoreDeveloper:
    """
    Internal user who develops and deploys opensafely core framework code.
    """

    permissions = [
        cancel_job,
        run_job,
    ]


class DataInvestigator:
    """
    Has access to Level 2 pseudonymised data, typically over a SQL browser, to
    understand and debug raw underlying data. Sometimes a core developer, and
    in rare and exceptional cases, a study developer.  Typically DataLab staff
    only.
    """

    permissions = []


class GovernanceReviewer:
    """
    IG, COPI coverage, and ethics for each project by each team, currently this
    is performed by NHSE.
    """

    permissions = []


class OnboardingAgent:
    """
    A developer and/or developer-researcher from the OpenSAFELY team with deep
    knowledge of OpenSAFELY who is providing ongoing collaborative technical,
    data science, analysis and academic support to external users who are
    delivering a project, to a degree that has been pre-planned and resourced.
    """

    permissions = []


class OutputChecker:
    """
    Review output folders that have been proposed for release.
    """

    permissions = [
        check_output,
    ]


class OutputPublisher:
    """
    Release approved-only outputs to a public location based on the work of the
    output checkers and/or an OpenSAFELY Reviewer.
    """

    permissions = [
        publish_output,
    ]


class ProjectCollaborator:
    """
    TODO: Define this role.
    """

    permissions = [
        "",
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

    permissions = [
        invite_project_members,
    ]


class ProjectDeveloper:
    """
    An external user who is developing and executing code to analyse data in
    OpenSAFELY; they will likely want to review (and flag for release) their
    own outputs.
    """

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

    permissions = []


class TechnicalReviewer:
    """
    Evaluation of the feasibility of the project and the skills of the
    applicants, by OpenSAFELY.
    """

    permissions = [
        review_project,
    ]
