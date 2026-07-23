import subprocess

import pytest
from django.core.management import call_command

from ..factories import UserFactory


@pytest.mark.slow_test
@pytest.mark.django_db(transaction=True)
def test_dump_raw_data_command_creates_valid_dump(tmp_path, slack_messages):
    """Check the command creates a dump containing data from the test database."""
    user = UserFactory()
    user.username = "TestPostgresDumpCommand"
    user.save()

    output_path = tmp_path / "test.dump"

    call_command(
        "dump_raw_data",
        output=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    result = subprocess.run(
        [
            "pg_restore",
            "--data-only",
            "--table",
            "jobserver_user",
            "--file=-",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    message, _ = slack_messages[0]

    assert user.username in result.stdout
    assert len(slack_messages) == 1
    assert (
        "Someone ran `dump_raw_data` to generate a raw Job Server database dump."
        in message
    )
    assert "bennett.wiki" in message
    assert (
        "The raw dump must be removed from the server and developer machines as soon as it is no longer required."
        in message
    )
