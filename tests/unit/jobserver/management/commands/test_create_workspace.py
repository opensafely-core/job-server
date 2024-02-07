import pytest
from django.core.management import CommandError, call_command

from jobserver.models import Workspace
from tests.factories.user import UserFactory


def test_create_workspace_defaults(capsys):
    user = UserFactory()
    call_command("create_workspace", "workspace", user.username)

    workspace = Workspace.objects.get(name="workspace")

    assert workspace.project.slug == "workspace"
    assert workspace.repo.url == "/org/workspace"

    # test idempotency
    call_command("create_workspace", "workspace", user.username)


def test_create_workspace_args(capsys):
    user = UserFactory()
    call_command(
        "create_workspace",
        "workspace",
        user.username,
        "--project=project",
        "--repo=/other/url",
    )

    workspace = Workspace.objects.get(name="workspace")

    assert workspace.project.slug == "project"
    assert workspace.repo.url == "/other/url"


def test_create_workspace_user_not_exist():
    with pytest.raises(CommandError):
        call_command("create_workspace", "workspace", "doesnotexist")
