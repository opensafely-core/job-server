import pytest
import responses
import responses.matchers
from django.core.management import CommandError, call_command

from jobserver.management.commands.check_rap_api_status import Command as cd
from tests.conftest import RAP_API_BASE_URL


TEST_STATUS_URL = f"{RAP_API_BASE_URL}backend/status/"
TEST_RESPONSE_BODY = b'{"backends":[{"name":"test","last_seen":{"since":"2025-08-12T06:57:43.039078Z"},"paused":{"status":"off","since":"2025-08-12T14:33:57.413881Z"},"db_maintenance":{"status":"off","since":null,"type":null}}]}'


def test_check_rap_api_status(rap_api_token):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            body=TEST_RESPONSE_BODY,
            match=[responses.matchers.header_matcher({"Authorization": rap_api_token})],
            status=200,
        )

        result = cd.check_rap_api_status()
        assert result == TEST_RESPONSE_BODY


def test_check_rap_api_status_bad_token(rap_api_token):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            match=[responses.matchers.header_matcher({"Authorization": rap_api_token})],
            status=401,
        )

        with pytest.raises(CommandError, match="returned an error"):
            cd.check_rap_api_status()


def test_check_rap_api_status_not_available():
    # Ask responses to intercept requests, but do not define any
    with responses.RequestsMock():
        with pytest.raises(CommandError, match="not available"):
            cd.check_rap_api_status()


def test_check_rap_api_status_env_vars_not_set(settings):
    # override the autouse rap_api_base_url and rap_api_token fixtures
    settings.RAP_API_TOKEN = ""
    settings.RAP_API_BASE_URL = ""

    # settings errors are the first raised
    with responses.RequestsMock():
        with pytest.raises(
            CommandError, match="RAP_API_BASE_URL and RAP_API_TOKEN are not set"
        ):
            cd.check_rap_api_status()


def test_command(rap_api_token, log_output):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            TEST_STATUS_URL,
            body=TEST_RESPONSE_BODY,
            match=[responses.matchers.header_matcher({"Authorization": rap_api_token})],
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
