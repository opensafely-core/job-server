import pytest
import responses
import responses.matchers
from django.conf import settings
from django.core.management import CommandError, call_command

from jobserver.management.commands.check_rap_api_status import Command as cd


def test_check_rap_api_status():
    with responses.RequestsMock() as rsps:
        # default rap api url
        url = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        rsps.add(
            responses.GET,
            f"{url}/backend/status",
            body=b'{"method": "GET"}',
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=200,
        )

        result = cd.check_rap_api_status(url, api_token)
        assert result == b'{"method": "GET"}'


def test_check_rap_api_status_bad_token():
    with responses.RequestsMock() as rsps:
        # default rap api url
        url = settings.RAP_API_ENDPOINT
        api_token = "badtoken"

        rsps.add(
            responses.GET,
            f"{url}/backend/status",
            body=b'{"method": "GET"}',
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=401,
        )

        with pytest.raises(CommandError, match="returned an error"):
            cd.check_rap_api_status(url, api_token)


def test_check_rap_api_status_not_available():
    # Ask responses to intercept requests, but do not define any
    with responses.RequestsMock():
        # default rap api url
        url = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        with pytest.raises(CommandError, match="not available"):
            cd.check_rap_api_status(url, api_token)


def test_command(capsys, log_output):
    with responses.RequestsMock() as rsps:
        # default rap api url
        url = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        rsps.add(
            responses.GET,
            f"{url}/backend/status",
            body=b'{"method": "GET"}',
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=200,
        )
        call_command("check_rap_api_status")

        assert log_output.entries[0] == {
            "event": b'{"method": "GET"}',
            "log_level": "info",
        }
