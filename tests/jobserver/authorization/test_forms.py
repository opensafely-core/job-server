from jobserver.authorization import ProjectCoordinator, ProjectDeveloper
from jobserver.authorization.forms import RolesForm


class DummyForm(RolesForm):
    pass


def test_rolesform_creation():
    form = RolesForm(
        initial={"roles": [ProjectCoordinator]},
        roles=[ProjectCoordinator, ProjectDeveloper],
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
        roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert not form.is_valid()
    assert form.errors["roles"] == [
        "Select a valid choice. test is not one of the available choices."
    ]


def test_rolesform_invalid_roles():
    form = RolesForm(
        data={"roles": ["test"]},
        initial={"roles": [ProjectCoordinator]},
        roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert not form.is_valid()
    assert form.errors["roles"] == [
        "Select a valid choice. test is not one of the available choices."
    ]


def test_rolesform_produces_role_classes():
    form = RolesForm(
        data={"roles": ["jobserver.authorization.roles.ProjectDeveloper"]},
        initial={"roles": [ProjectCoordinator]},
        roles=[ProjectCoordinator, ProjectDeveloper],
    )

    assert form.is_valid(), form.errors

    assert form.cleaned_data["roles"] == [ProjectDeveloper]
