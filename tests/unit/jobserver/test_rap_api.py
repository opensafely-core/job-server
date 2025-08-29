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
    RapAPIRequestError,
    RapAPIResponseError,
    RapAPISettingsError,
    _api_call,
    backend_status,
    cancel,
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

        # Using a fake method here helps avoid conflating issues about how we invoke
        # the actual requests methods with issues in the _api_call code.
        # Note that this magic method name is specifically allowed in api_call.
        def fake_request_method(*args, **kwargs):
            raise requests.exceptions.RequestException("boom")

        with pytest.raises(RapAPIRequestError):
            _api_call(fake_request_method, "some/path/")

    def test_success_fake_request_method(self, rap_api_base_url, rap_api_token):
        """Test that a fake request_method is called as expected."""
        path = "some/path/"
        json = {"foo": "bar"}

        # Using a fake method here helps avoid conflating issues about how we invoke
        # the actual requests methods with issues in the _api_call code.
        # Note that this magic method name is specifically allowed in api_call.
        def fake_request_method(url, **kwargs):
            return (url, kwargs)

        response = _api_call(fake_request_method, "some/path/", json=json)

        assert response[0] == f"{rap_api_base_url}{path}"
        assert response[1]["json"] == json
        assert response[1]["headers"] == {"Authorization": rap_api_token}

    def test_success_fake_request_method_no_json(self, rap_api_base_url, rap_api_token):
        """Test that a fake request_method is called as expected with no json
        parameter."""
        path = "some/path/"

        # Using a fake method here helps avoid conflating issues about how we invoke
        # the actual requests methods with issues in the _api_call code.
        # Note that this magic method name is specifically allowed in api_call.
        def fake_request_method(url, **kwargs):
            return (url, kwargs)

        response = _api_call(fake_request_method, "some/path/")

        assert response[0] == f"{rap_api_base_url}{path}"
        assert response[1]["json"] is None
        assert response[1]["headers"] == {"Authorization": rap_api_token}

    def test_disallowed_method(self):
        """Test that a disallowed request_method raises right Exception."""
        path = "some/path/"
        with pytest.raises(ValueError, match="request_method not allowed"):
            _api_call(requests.put, path)

    def test_requests_get(self, rap_api_base_url, rap_api_token):
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

    def test_headers_requests_post(self, rap_api_base_url, rap_api_token):
        """Test that the actual requests.post method handles headers and body correctly."""
        path = "some/path/"
        request_body = {"hello": "world"}
        response_body = {"foo": 123}

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{rap_api_base_url}{path}",
                json=response_body,
                status=200,
                match=[
                    responses.matchers.header_matcher({"Authorization": rap_api_token}),
                    responses.matchers.json_params_matcher(request_body),
                ],
            )
            response = _api_call(requests.post, path, json=request_body)

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


class TestCancel:
    """Tests of cancel.

    This just returns the response and doesn't distinguish between non-200
    error codes, so these are pretty simple."""

    _fake_args = ("abcde1234", ["action1", "action2"])

    def test_success(self, patch_api_call):
        """Test content from api_call returned."""
        fake_json = {"some": "content"}
        patch_api_call(fake_json)

        assert cancel(*self._fake_args) == fake_json

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_json = {"err": "some problem detected"}
        patch_api_call(fake_json, status_code=400)

        with pytest.raises(RapAPIResponseError) as exc:
            cancel(*self._fake_args)
        assert exc.value.body == fake_json
