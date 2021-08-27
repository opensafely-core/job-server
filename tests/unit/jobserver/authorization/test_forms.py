from jobserver.authorization import ProjectCoordinator, ProjectDeveloper
from jobserver.authorization.forms import RolesForm


def test_rolesform_creation():
    form = RolesForm(
        initial={"roles": [ProjectCoordinator]},
        available_roles=[ProjectCoordinator, ProjectDeveloper],
    )

    choices = form.fields["roles"].choices
    assert (
        "jobserver.authorization.roles.ProjectDeveloper",
        "Project Developer",
    ) in choices

    initial = form.fields["roles"].initial
    assert initial == ["jobserver.authorization.roles.ProjectCoordinator"]


def test_rolesform_no_initial():
    form = RolesForm(
        data={"roles": ["test"]},
        available_roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert not form.is_valid()
    assert form.errors["roles"] == [
        "Select a valid choice. test is not one of the available choices."
    ]


def test_rolesform_invalid_roles():
    form = RolesForm(
        data={"roles": ["test"]},
        initial={"roles": [ProjectCoordinator]},
        available_roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert not form.is_valid()
    assert form.errors["roles"] == [
        "Select a valid choice. test is not one of the available choices."
    ]


def test_rolesform_produces_role_classes():
    form = RolesForm(
        data={"roles": ["jobserver.authorization.roles.ProjectDeveloper"]},
        initial={"roles": [ProjectCoordinator]},
        available_roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert form.is_valid(), form.errors

    assert form.cleaned_data["roles"] == [ProjectDeveloper]


def test_rolesform_with_no_roles():
    form = RolesForm(
        available_roles=[ProjectCoordinator],
        data={"roles": []},
    )

    assert form.is_valid()
    assert len(form.cleaned_data["roles"]) == 0
