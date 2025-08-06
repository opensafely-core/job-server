import pytest
import responses
import responses.matchers
from django.conf import settings
from django.core.management import CommandError, call_command

from jobserver.management.commands.check_rap_api_status import Command as cd


TEST_BASE_URL = settings.RAP_API_BASE_URL
TEST_STATUS_URL = f"{TEST_BASE_URL}/backend/status"
TEST_API_TOKEN = settings.RAP_API_TOKEN
TEST_RESPONSE_BODY = b'{"flags":{"test":{"paused":{"v":null,"ts":"2025-05-09T15:05:09.010195Z"},"last-seen-at":{"v":"2025-07-18T09:29:20.504634+00:00","ts":"2025-07-18T09:29:20.504842Z"}}}}'


def test_check_rap_api_status():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            body=TEST_RESPONSE_BODY,
            match=[
                responses.matchers.header_matcher({"Authorization": TEST_API_TOKEN})
            ],
            status=200,
        )

        result = cd.check_rap_api_status(TEST_BASE_URL, TEST_API_TOKEN)
        assert result == TEST_RESPONSE_BODY


def test_check_rap_api_status_bad_token():
    with responses.RequestsMock() as rsps:
        api_token_bad = "badtoken"

        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            match=[responses.matchers.header_matcher({"Authorization": api_token_bad})],
            status=401,
        )

        with pytest.raises(CommandError, match="returned an error"):
            cd.check_rap_api_status(TEST_BASE_URL, api_token_bad)


def test_check_rap_api_status_not_available():
    # Ask responses to intercept requests, but do not define any
    with responses.RequestsMock():
        with pytest.raises(CommandError, match="not available"):
            cd.check_rap_api_status(TEST_BASE_URL, TEST_API_TOKEN)


def test_command(log_output):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            body=TEST_RESPONSE_BODY,
            match=[
                responses.matchers.header_matcher({"Authorization": TEST_API_TOKEN})
            ],
            status=200,
        )
        call_command("check_rap_api_status")

        assert log_output.entries[0] == {
            "event": TEST_RESPONSE_BODY,
            "log_level": "info",
        }


def test_command_error(log_output):
    with responses.RequestsMock():
        call_command("check_rap_api_status")

        assert "error" == log_output.entries[0]["log_level"]
        assert "not available" in str(log_output.entries[0]["event"])
