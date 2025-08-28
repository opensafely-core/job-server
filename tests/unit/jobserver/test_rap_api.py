"""Unit tests of jobserver.rap_api.

It is a design goal of this module that the unit tests of the clients of the
endpoint functions should not need to know anything about how we actually make
the API call. They should mock the endpoint functions to return the required
objects or exceptions. They should not be patching the requests module.

When adding an endpoint make sure that the request method you use has tests for
it in TestAPICall."""

import pytest
import requests
import responses
import responses.matchers

from jobserver.rap_api import (
    RapAPICommunicationError,
    RapAPIResponseError,
    RapAPISettingsError,
    _api_call,
    backend_status,
)


class TestApiCall:
    """Tests of api_call. Separating the commonality allows the individual
    endpoint function tests to focus on the response status code and body,
    which they should mock using patch_api_call."""

    def test_missing_url_setting(self, settings):
        """Test that missing the URL setting raises right Exception."""
        settings.RAP_API_BASE_URL = None
        with pytest.raises(RapAPISettingsError):
            _api_call(requests.get, "some/path/")

    def test_missing_token_setting(self, settings):
        """Test that missing the token setting raises right Exception."""
        settings.RAP_API_TOKEN = None
        with pytest.raises(RapAPISettingsError):
            _api_call(requests.get, "some/path/")

    def test_missing_both_settings(self, settings):
        """Test that missing both settings raises right Exception."""
        settings.RAP_API_BASE_URL = None
        settings.RAP_API_TOKEN = None
        with pytest.raises(RapAPISettingsError):
            _api_call(requests.get, "some/path/")

    def test_request_exception(self):
        """Test that a requests module RequestException is transformed and re-raised."""

        def fake_request_method(*args, **kwargs):
            raise requests.exceptions.RequestException("boom")

        with pytest.raises(RapAPICommunicationError):
            _api_call(fake_request_method, "some/path/")

    def test_success_fake_request_method(self, rap_api_base_url, rap_api_token):
        """Test that a fake request_method is called as expected."""
        path = "some/path/"

        # Using a fake method here helps avoid conflating issues about how we invoke
        # the actual requests methods with issues in the _api_call code.
        def fake_request_method(url, **kwargs):
            return (url, kwargs)

        response = _api_call(fake_request_method, "some/path/")

        assert response[0] == f"{rap_api_base_url}{path}"
        assert response[1]["headers"] == {"Authorization": rap_api_token}

    def test_headers_requests_get(self, rap_api_base_url, rap_api_token):
        """Test that the actual requests.get method handles headers correctly."""
        path = "some/path/"
        response_body = {"foo": 123}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{rap_api_base_url}{path}",
                json=response_body,
                status=200,
                match=[
                    responses.matchers.header_matcher({"Authorization": rap_api_token})
                ],
            )
            response = _api_call(requests.get, path)
        assert response.status_code == 200
        assert response.json() == response_body


class FakeResponse:
    """Lightweight fake response similar enough to requests.Response for these tests."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


@pytest.fixture
def patch_api_call(monkeypatch):
    """
    Fixture to patch _api_call with a fake response. Use this to test the
    individual endpoint functions. TestApiCall has tests of _api_call and that
    the requests methods are applied as expected.

    Usage:
        patch_api_call(fake_json, status_code=200)
    """

    def _do_patch(fake_json=None, status_code=200):
        fake_response = FakeResponse(fake_json, status_code=status_code)
        monkeypatch.setattr(
            "jobserver.rap_api._api_call", lambda *args, **kwargs: fake_response
        )
        return fake_response

    return _do_patch


class TestBackendStatus:
    """Tests of backend_status.

    This just returns the response and doesn't distinguish between non-200
    error codes, so these are pretty simple."""

    def test_success(self, patch_api_call):
        """Test content from api_call returned."""
        fake_json = {"some": "content"}
        patch_api_call(fake_json)

        assert backend_status() == fake_json

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200 status raises right Exception."""
        patch_api_call(status_code=500)

        with pytest.raises(RapAPIResponseError):
            backend_status()
