import pytest
import responses
import responses.matchers
from _pytest.fixtures import fixture
from django.conf import settings
from django.core.management import CommandError, call_command

from jobserver.management.commands.check_rap_api_status import Command as cd


@fixture
def endpoint():
    return settings.RAP_API_ENDPOINT


@fixture
def status_url(endpoint):
    return f"{endpoint}/backend/status"


@fixture
def api_token():
    return settings.RAP_API_TOKEN


@fixture
def response_body():
    return b'{"flags":{"test":{"paused":{"v":null,"ts":"2025-05-09T15:05:09.010195Z"},"last-seen-at":{"v":"2025-07-18T09:29:20.504634+00:00","ts":"2025-07-18T09:29:20.504842Z"}}}}'


def test_check_rap_api_status(endpoint, status_url, api_token, response_body):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            status_url,
            body=response_body,
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=200,
        )

        result = cd.check_rap_api_status(endpoint, api_token)
        assert result == response_body


def test_check_rap_api_status_bad_token(endpoint, status_url):
    with responses.RequestsMock() as rsps:
        api_token_bad = "badtoken"

        rsps.add(
            responses.GET,
            status_url,
            match=[responses.matchers.header_matcher({"Authorization": api_token_bad})],
            status=401,
        )

        with pytest.raises(CommandError, match="returned an error"):
            cd.check_rap_api_status(endpoint, api_token_bad)


def test_check_rap_api_status_not_available(endpoint, status_url, api_token):
    # Ask responses to intercept requests, but do not define any
    with responses.RequestsMock():
        with pytest.raises(CommandError, match="not available"):
            cd.check_rap_api_status(endpoint, api_token)


def test_command(endpoint, status_url, api_token, response_body, log_output):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            status_url,
            body=response_body,
            match=[responses.matchers.header_matcher({"Authorization": api_token})],
            status=200,
        )
        call_command("check_rap_api_status")

        assert log_output.entries[0] == {
            "event": response_body,
            "log_level": "info",
        }


def test_command_error(endpoint, status_url, api_token, log_output):
    with responses.RequestsMock():
        call_command("check_rap_api_status")

        assert "error" == log_output.entries[0]["log_level"]
        assert "not available" in str(log_output.entries[0]["event"])
