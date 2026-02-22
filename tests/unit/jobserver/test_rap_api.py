"""Unit tests of jobserver.rap_api.

It is a design goal of this module that the unit tests of the clients of the
endpoint functions should not need to know anything about how we actually make
the API call. They should mock the endpoint functions to return the required
objects or exceptions. They should not be patching the requests module.

When adding an endpoint make sure that the request method you use has tests for
it in TestAPICall."""

import json
from unittest.mock import Mock

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
    create,
    status,
)
from tests.factories import JobRequestFactory, ProjectFactory, WorkspaceFactory


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

        response = _api_call(fake_request_method, path, json=json)

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

        response = _api_call(fake_request_method, path)

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

    def test_request_get_and_json(self):
        """Test that request_method requests.get disallowed with JSON parameter.

        A payload within a GET request message has no defined semantics.
        """
        path = "some/path/"
        with pytest.raises(ValueError, match="requests.get and json parameter"):
            _api_call(requests.get, path, json={})

    def test_requests_post(self, rap_api_base_url, rap_api_token):
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

    # Nb. content should be bytes as per
    # https://docs.python-requests.org/en/latest/api/#requests.Response.content
    def __init__(self, content=None, json_data=None, status_code=200):
        if content and json_data:
            raise ValueError("Tests should only specify content *or* json_data")

        if content:
            self.content = content
        else:
            self.content = json.dumps(json_data).encode("utf-8")
        self.status_code = status_code

    def json(self):
        return json.loads(self.content.decode("utf-8"))


class TestFakeResponse:
    def test_not_both_content_and_json_data(self):
        with pytest.raises(ValueError):
            FakeResponse(content="bad", json_data={"bad": "yes"})


@pytest.fixture
def patch_api_call(monkeypatch):
    """
    Fixture to patch _api_call with a fake response. Use this to test the
    individual endpoint functions. TestApiCall has tests of _api_call and that
    the requests methods are applied as expected.

    Usage:
        patch_api_call(fake_json=fake_json, status_code=200)
        patch_api_call(fake_body=fake_body, status_code=500)

    Returns:
        called: dict with params the tested function called api_call with
    """

    def _do_patch(*, fake_body=None, fake_json=None, status_code=200):
        if fake_json:
            fake_response = FakeResponse(json_data=fake_json, status_code=status_code)
        else:
            fake_response = FakeResponse(content=fake_body, status_code=status_code)

        mock_api_call = Mock(
            return_value=fake_response,
            spec=["__call__", "assert_called_once_with"],
        )
        monkeypatch.setattr("jobserver.rap_api._api_call", mock_api_call)
        return mock_api_call

    return _do_patch


class TestBackendStatus:
    """Tests of backend_status.

    This just returns the response and doesn't distinguish between non-200
    error codes, so these are pretty simple."""

    def test_success(self, patch_api_call):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json)
        result = backend_status()

        assert result == fake_json
        mock_api_call.assert_called_once_with(requests.get, "backend/status/")

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200 status raises right Exception."""
        fake_body = b"<html>Gateway Error 500</html>"
        patch_api_call(fake_body=fake_body, status_code=500)

        with pytest.raises(RapAPIResponseError):
            backend_status()


class TestCancel:
    """Tests of cancel.

    This just returns the response and doesn't distinguish between non-200
    error codes, so these are pretty simple."""

    _fake_args = ("abcde1234", ["action1", "action2"])

    def test_success(self, patch_api_call):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json)
        result = cancel(*self._fake_args)

        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/cancel/",
            {
                "rap_id": self._fake_args[0],
                "actions": self._fake_args[1],
            },
        )

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_json = {"err": "some problem detected", "details": "gory"}
        patch_api_call(fake_json=fake_json, status_code=400)

        with pytest.raises(RapAPIResponseError, match="gory") as exc:
            cancel(*self._fake_args)
        assert exc.value.body == fake_json

    def test_bad_status_code_500(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_body = b"<html>Gateway Error 500</html>"
        patch_api_call(fake_body=fake_body, status_code=500)

        with pytest.raises(RapAPIResponseError) as exc:
            cancel(*self._fake_args)
        assert exc.value.body == fake_body


class TestStatus:
    """Tests of status.

    This just returns the response and doesn't distinguish between non-200
    error codes, so these are pretty simple."""

    _fake_args = ["abcdefgh12345678"]

    def test_success(self, patch_api_call):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"jobs": [{"identifier": "abcdefgh12345678"}]}
        mock_api_call = patch_api_call(fake_json=fake_json)
        result = status(self._fake_args)

        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/status/",
            {
                "rap_ids": self._fake_args,
            },
        )

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_json = {"err": "some problem detected"}
        patch_api_call(fake_json=fake_json, status_code=400)

        with pytest.raises(RapAPIResponseError) as exc:
            status(*self._fake_args)
        assert json.loads(exc.value.body) == fake_json

    def test_bad_status_code_500(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_body = b"<html>Gateway Error 500</html>"
        patch_api_call(fake_body=fake_body, status_code=500)

        with pytest.raises(RapAPIResponseError) as exc:
            status(*self._fake_args)
        assert exc.value.body == fake_body


@pytest.fixture
def job_request_for_create():
    # Ensure this job_request has a project with a number (by default it will be None)
    # so that it can be looked up in the project-specific permissions files that
    # determine the value of the analysis_scope request parameter
    project = ProjectFactory(number=111)
    workspace = WorkspaceFactory(project=project)
    job_request = JobRequestFactory(workspace=workspace)

    request_body = {
        "rap_id": job_request.identifier,
        "backend": job_request.backend.slug,
        "workspace": job_request.workspace.name,
        "repo_url": job_request.workspace.repo.url,
        "branch": job_request.workspace.branch,
        "commit": job_request.sha,
        "database_name": job_request.database_name,
        "requested_actions": job_request.requested_actions,
        "codelists_ok": job_request.codelists_ok,
        "force_run_dependencies": job_request.force_run_dependencies,
        "created_by": job_request.created_by.username,
        "project": job_request.workspace.project.slug,
        "orgs": list(job_request.workspace.project.orgs.values_list("slug", flat=True)),
        "analysis_scope": {},
    }
    yield job_request, request_body


class TestCreate:
    """Tests of cancel.

    This just returns the response and doesn't distinguish between non-200/201
    error codes, so these are pretty simple."""

    def test_success_200(self, monkeypatch, patch_api_call, job_request_for_create):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json)

        job_request, expected_request_body = job_request_for_create

        # mock ndoo permission to ensure that our mock project (number 111) does not have permission
        # this means the api will be called with `"analysis_scope": {}` in the request body
        monkeypatch.setattr(
            "jobserver.permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION",
            [222, 333],
        )

        result = create(job_request)

        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/create/",
            expected_request_body,
        )

    def test_success_201(self, monkeypatch, patch_api_call, job_request_for_create):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 201."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json, status_code=201)

        job_request, expected_request_body = job_request_for_create

        # mock ndoo permission to ensure that our mock project (number 111) does not have permission
        # this means the api will be called with `"analysis_scope": {}` in the request body
        monkeypatch.setattr(
            "jobserver.permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION",
            [],
        )
        result = create(job_request)

        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/create/",
            expected_request_body,
        )

    def test_population_permissions(
        self, monkeypatch, patch_api_call, job_request_for_create
    ):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json)

        job_request, expected_request_body = job_request_for_create
        # mock ndoo and gp_activations permissions to ensure this job's project has permission
        # with no permission, the request body will send `"analysis_scop": {}`
        monkeypatch.setattr(
            "jobserver.permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION",
            [str(job_request.workspace.project.number)],
        )
        monkeypatch.setattr(
            "jobserver.permissions.population_permissions.gp_activations.PROJECTS_WITH_GP_ACTIVATIONS_PERMISSION",
            [str(job_request.workspace.project.number)],
        )
        # update request body with expected analysis scope
        expected_request_body["analysis_scope"] = {
            "population_permissions": ["include_ndoo", "include_gp_unactivated"]
        }

        result = create(job_request)
        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/create/",
            expected_request_body,
        )

    def test_population_permissions_with_slug(self, monkeypatch, patch_api_call):
        """Test api_call is called with expected parameters and its body
        returned when it returns a 200."""
        fake_json = {"some": "content"}
        mock_api_call = patch_api_call(fake_json=fake_json)

        # Create a project with no number, so we will look up permission by slug
        project = ProjectFactory()
        assert project.number is None
        workspace = WorkspaceFactory(project=project)
        job_request = JobRequestFactory(workspace=workspace)

        expected_request_body = {
            "rap_id": job_request.identifier,
            "backend": job_request.backend.slug,
            "workspace": job_request.workspace.name,
            "repo_url": job_request.workspace.repo.url,
            "branch": job_request.workspace.branch,
            "commit": job_request.sha,
            "database_name": job_request.database_name,
            "requested_actions": job_request.requested_actions,
            "codelists_ok": job_request.codelists_ok,
            "force_run_dependencies": job_request.force_run_dependencies,
            "created_by": job_request.created_by.username,
            "project": job_request.workspace.project.slug,
            "orgs": list(
                job_request.workspace.project.orgs.values_list("slug", flat=True)
            ),
            "analysis_scope": {"population_permissions": ["include_ndoo"]},
        }

        # mock ndoo permission to ensure this job's project has permission
        monkeypatch.setattr(
            "jobserver.permissions.population_permissions.ndoo.PROJECTS_WITH_NDOO_PERMISSION",
            [job_request.workspace.project.slug],
        )

        result = create(job_request)
        assert result == fake_json
        mock_api_call.assert_called_once_with(
            requests.post,
            "rap/create/",
            expected_request_body,
        )

    def test_bad_status_code(self, patch_api_call):
        """Test a non-200/201 status raises right Exception including the response body."""
        fake_json = {"err": "some problem detected", "details": "Couldn't do it"}
        patch_api_call(fake_json=fake_json, status_code=400)

        job_request = JobRequestFactory()

        with pytest.raises(RapAPIResponseError) as exc:
            create(job_request)
        assert exc.value.body == fake_json

    def test_bad_status_code_500(self, patch_api_call):
        """Test a non-200 status raises right Exception including the response body."""
        fake_body = b"<html>Gateway Error 500</html>"
        patch_api_call(fake_body=fake_body, status_code=500)

        job_request = JobRequestFactory()

        with pytest.raises(RapAPIRequestError):
            create(job_request)
