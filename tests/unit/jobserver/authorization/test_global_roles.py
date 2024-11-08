from jobserver.authorization.global_roles import GLOBAL_ROLE_NAMES


def test_global_role_names():
    assert set(GLOBAL_ROLE_NAMES) & set(
        [
            "DeploymentAdministrator",
            "InteractiveReporter",
            "OutputChecker",
            "OutputPublisher",
            "ProjectCollaborator",
            "SignOffRepoWithOutputs",
            "StaffAreaAdministrator",
        ]
    )
