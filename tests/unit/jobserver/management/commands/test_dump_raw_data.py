import os
import subprocess
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


TEST_HOST = "test_host"
TEST_PORT = "test_port"
TEST_USER = "test_user"
TEST_PASSWORD = "test_pass"
TEST_DBNAME = "test_dbname"


@pytest.fixture
def fake_database_settings(monkeypatch, tmp_path):
    fake_settings = SimpleNamespace(
        DATABASES={
            "default": {
                "HOST": TEST_HOST,
                "PORT": TEST_PORT,
                "USER": TEST_USER,
                "PASSWORD": TEST_PASSWORD,
                "NAME": TEST_DBNAME,
            }
        },
        RAW_DATABASE_DUMP_PATH=tmp_path / "jobserver.dump",
    )

    monkeypatch.setattr(
        "jobserver.management.commands.dump_raw_data.settings", fake_settings
    )

    return fake_settings


@pytest.fixture
def fake_subprocess_calls(monkeypatch):
    calls = []

    def fake_run(command, env, capture_output, text, check):
        calls.append(
            {
                "command": command,
                "env": env,
                "capture_output": capture_output,
                "text": text,
                "check": check,
            }
        )

    monkeypatch.setattr(
        "jobserver.management.commands.dump_raw_data.subprocess.run",
        fake_run,
    )

    return calls


def test_dump_raw_data_command_with_default_path(
    fake_database_settings, fake_subprocess_calls, capsys
):
    call_command("dump_raw_data")

    output_path = fake_database_settings.RAW_DATABASE_DUMP_PATH
    assert fake_subprocess_calls == [
        {
            "command": [
                "pg_dump",
                "--format=c",
                "--no-acl",
                "--no-owner",
                f"--file={output_path}",
                "--host",
                TEST_HOST,
                "--port",
                TEST_PORT,
                "--username",
                TEST_USER,
                "--dbname",
                TEST_DBNAME,
            ],
            "env": {
                "PATH": os.environ["PATH"],
                "PGPASSWORD": TEST_PASSWORD,
            },
            "capture_output": True,
            "text": True,
            "check": True,
        }
    ]

    out, _ = capsys.readouterr()
    assert f"Creating raw JobServer database dump at {output_path}" in out
    assert f"Finished creating raw JobServer database dump at {output_path}" in out


def test_dump_raw_data_command_with_custom_path(
    fake_database_settings, fake_subprocess_calls, tmp_path
):
    output_path = tmp_path / "custom.dump"

    call_command("dump_raw_data", "--output", str(output_path))

    assert fake_subprocess_calls[0]["command"][4] == f"--file={output_path}"


def test_dump_raw_data_command_error(fake_database_settings, monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["pg_dump"],
            output="stdout",
            stderr="stderr",
        )

    monkeypatch.setattr(
        "jobserver.management.commands.dump_raw_data.subprocess.run",
        fake_run,
    )

    with pytest.raises(CommandError, match="pg_dump failed") as error:
        call_command("dump_raw_data")

    assert "returncode=1" in str(error.value)
    assert "stdout=stdout" in str(error.value)
    assert "stderr=stderr" in str(error.value)
