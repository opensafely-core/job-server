import os
import subprocess

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


TEST_HOST = "test_host"
TEST_PORT = "test_port"
TEST_USER = "test_user"
TEST_PASSWORD = "test_pass"
TEST_DBNAME = "test_dbname"


@pytest.fixture
def default_database(settings):
    database_config = {
        "HOST": TEST_HOST,
        "PORT": TEST_PORT,
        "USER": TEST_USER,
        "PASSWORD": TEST_PASSWORD,
        "NAME": TEST_DBNAME,
    }
    settings.DATABASES["default"] = database_config
    return database_config


def test_dump_raw_data_command(
    settings, default_database, monkeypatch, tmp_path, capsys
):
    settings.RAW_DATABASE_DUMP_PATH = tmp_path / "jobserver.dump"
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

    call_command("dump_raw_data")

    assert calls == [
        {
            "command": [
                "pg_dump",
                "--format=c",
                "--no-acl",
                "--no-owner",
                f"--file={tmp_path / 'jobserver.dump'}",
                "--host",
                default_database["HOST"],
                "--port",
                default_database["PORT"],
                "--username",
                default_database["USER"],
                "--dbname",
                default_database["NAME"],
            ],
            "env": {
                "PATH": os.environ["PATH"],
                "PGPASSWORD": default_database["PASSWORD"],
            },
            "capture_output": True,
            "text": True,
            "check": True,
        }
    ]

    out, _ = capsys.readouterr()
    assert (
        f"Creating raw JobServer database dump at {tmp_path / 'jobserver.dump'}" in out
    )
    assert (
        f"Finished creating raw JobServer database dump at {tmp_path / 'jobserver.dump'}"
        in out
    )


def test_dump_raw_data_command_with_custom_path(
    default_database, monkeypatch, tmp_path
):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)

    monkeypatch.setattr(
        "jobserver.management.commands.dump_raw_data.subprocess.run",
        fake_run,
    )

    output_path = tmp_path / "custom.dump"
    call_command("dump_raw_data", "--output", str(output_path))

    assert calls[0][4] == f"--file={output_path}"


def test_command_error(settings, default_database, monkeypatch, tmp_path):
    settings.RAW_DATABASE_DUMP_PATH = tmp_path / "jobserver.dump"

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
