from unittest.mock import patch

from django.core.management import call_command


@patch("jobserver.management.commands.rap_status.rap_status_update", autospec=True)
def test_call_rap_status_command(mock_rap_status_update):
    call_command("rap_status", "identifier")

    mock_rap_status_update.assert_called_once_with(["identifier"])


@patch("jobserver.management.commands.rap_status.rap_status_update", autospec=True)
def test_command_error(mock_rap_status_update, log_output):
    mock_rap_status_update.side_effect = Exception("something went wrong")

    call_command("rap_status", "abcdefgi12345678")

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])
