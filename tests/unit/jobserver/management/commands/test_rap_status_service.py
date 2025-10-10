from unittest.mock import Mock, patch

from django.core.management import call_command


@patch(
    "jobserver.management.commands.rap_status_service.rap_status_update", autospec=True
)
@patch(
    "jobserver.management.commands.rap_status_service.get_active_job_request_identifiers",
    autospec=True,
)
def test_call_rap_status_service_command(
    mock_get_active_job_request_ids, mock_rap_status_update, settings
):
    settings.RAP_API_POLL_INTERVAL = 0
    mock_get_active_job_request_ids.return_value = ["identifier"]
    # Mock run_fn so we loop twice then stop
    run_fn = Mock(side_effect=[True, True, False])
    call_command("rap_status_service", run_fn=run_fn)
    assert mock_rap_status_update.call_count == 2
    for call in mock_rap_status_update.call_args_list:
        assert call.args == (["identifier"],)


@patch(
    "jobserver.management.commands.rap_status_service.rap_status_update", autospec=True
)
@patch(
    "jobserver.management.commands.rap_status_service.get_active_job_request_identifiers",
    autospec=True,
)
def test_call_rap_status_service_command_error(
    mock_get_active_job_request_ids, mock_rap_status_update, settings, log_output
):
    settings.RAP_API_POLL_INTERVAL = 0

    # Mock an unhandled exception the first time get_active_job_request_identifiers is called
    mock_get_active_job_request_ids.side_effect = [Exception("bad ids"), ["identifier"]]

    # Mock run_fn so we loop twice then stop
    run_fn = Mock(side_effect=[True, True, False])

    call_command("rap_status_service", run_fn=run_fn)
    # rap_status_update is only called once, on the second loop when get_active_job_request_identifiers succeeded
    assert mock_rap_status_update.call_count == 1
    mock_rap_status_update.assert_called_with(["identifier"])

    assert "error" == log_output.entries[0]["log_level"]
    assert "bad ids" in str(log_output.entries[0]["event"])
