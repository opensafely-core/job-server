import pytest
from django.core.management import CommandError, call_command

from tests.factories import (
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_delete_project_missing_project_name():
    msg = "Error: the following arguments are required: project_name"

    with pytest.raises(CommandError, match=msg):
        call_command("delete_project")


def test_delete_project_success(capsys):
    ProjectFactory(name="test-project")

    call_command("delete_project", "test-project")

    captured = capsys.readouterr()
    assert captured.out == "Project test-project deleted\n"


def test_delete_project_doesnt_exist(capsys):
    with pytest.raises(SystemExit) as exc_info:
        call_command("delete_project", "no-project")

    assert exc_info.value.args[0] == "Project does not exist"


def test_delete_project_with_members(capsys, project_membership):
    project = ProjectFactory(name="test-project")
    user = UserFactory()
    project_membership(project=project, user=user)

    with pytest.raises(SystemExit) as exc_info:
        call_command("delete_project", "test-project")

    assert (
        exc_info.value.args[0]
        == "Unable to delete a project with workspaces or members"
    )


def test_delete_project_with_workspaces(capsys):
    project = ProjectFactory(name="test-project")
    WorkspaceFactory(project=project)

    with pytest.raises(SystemExit) as exc_info:
        call_command("delete_project", "test-project")

    assert (
        exc_info.value.args[0]
        == "Unable to delete a project with workspaces or members"
    )
