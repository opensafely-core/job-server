import jobserver.authorization.roles as roles_module
from jobserver.authorization.global_roles import (
    ALL_ROLES,
    GLOBAL_ROLE_NAMES,
    GLOBAL_ROLES,
    PROJECT_ROLES,
)
from jobserver.authorization.roles import (
    DeploymentAdministrator,
    OutputChecker,
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
    ServiceAdministrator,
    SignOffRepoWithOutputs,
    StaffAreaAdministrator,
    TechSupport,
)


def test_global_role_names():
    assert set(GLOBAL_ROLE_NAMES) == set(
        [
            "StaffAreaAdministrator",
            "TechSupport",
            "ServiceAdministrator",
            "OutputChecker",
            "OutputPublisher",
            "ProjectCollaborator",
            "SignOffRepoWithOutputs",
            "DeploymentAdministrator",
        ]
    )


def test_global_roles():
    assert set(GLOBAL_ROLES) == set(
        [
            StaffAreaAdministrator,
            TechSupport,
            ServiceAdministrator,
            OutputChecker,
            OutputPublisher,
            ProjectCollaborator,
            SignOffRepoWithOutputs,
            DeploymentAdministrator,
        ]
    )


def test_project_roles():
    assert set(PROJECT_ROLES) == set(
        [
            ProjectDeveloper,
            ProjectCollaborator,
        ]
    )


def test_all_roles():
    """Test that ALL_ROLES has all the roles from the roles module."""
    role_names_in_module = {
        role_name
        for role_name in dir(roles_module)
        # Exclude private attributes and the imported Permission class.
        if not role_name.startswith("_") and not role_name.startswith("Perm")
    }
    assert {role.__name__ for role in ALL_ROLES} == role_names_in_module
