import pytest
from django.core.management import CommandError, call_command


def test_create_bot_missing_username():
    msg = "Error: the following arguments are required: username"
    with pytest.raises(CommandError, match=msg):
        call_command("create_bot")


def test_create_bot_success(capsys):
    call_command("create_bot", "test-bot")

    captured = capsys.readouterr()

    assert captured.out.startswith("New token: test-bot:"), captured.out


def test_create_bot_with_existing_username(capsys):
    call_command("create_bot", "test-bot")

    with pytest.raises(SystemExit, match="User 'test-bot' already exists"):
        call_command("create_bot", "test-bot")
