"""Methods to interact with the RAP Controller via its API.

These allow control and query of Reproducible Analytics Pipelines executed in a
Backend to service a Job Request.

Reference for how the server defines the API endpoints:
https://controller.opensafely.org/controller/v1/docs/
https://github.com/opensafely-core/job-runner/tree/main/controller/webapp/api_spec

The functions corresponding to each endpoint should not leak HTTP-layer
information or the implementation detail that we use the requests library. So
they should return subclasses of RapAPIError for relevant status codes or other
errors, for example. They should probably not need to transform the response
body defined in the spec. Clients of this module will interpret those further.
"""

from urllib.parse import urljoin

import requests
from django.conf import settings


class RapAPIError(Exception):
    """Base exception for this module. A problem contacting or using the RAP
    API."""


class RapAPISettingsError(RapAPIError):
    """There was a problem with the relevant Django settings."""


class RapAPICommunicationError(RapAPIError):
    """A request to the RAP API failed to return a response."""


class RapAPIResponseError(RapAPIError):
    """A response to a RAP API request indicated an error."""

    def __init__(self, message, body=None):
        super().__init__(message)
        self.body = body


def _api_call(request_method, endpoint_path, json=None):
    """Communicate with a remote RAP API endpoint and return the response.

    Args:
        request_method: One of the requests.request HTTP helper methods.
        endpoint_path: Subpath of the endpoint. No leading slash.

    Raises:
        RapAPISettingsError
        RapAPICommunicationError
    """
    # Check the required settings early.
    if not (settings.RAP_API_BASE_URL and settings.RAP_API_TOKEN):
        raise RapAPISettingsError(
            "A required environment variable RAP_API_BASE_URL and/or RAP_API_TOKEN is not set"
        )

    # Do the request-response cycle.
    try:
        response = request_method(
            urljoin(settings.RAP_API_BASE_URL, endpoint_path),
            headers={"Authorization": settings.RAP_API_TOKEN},
            json=json,
        )
    except requests.exceptions.RequestException as exc:
        raise RapAPICommunicationError(f"RAP API endpoint not available: {exc}")

    return response


def backend_status():
    """
    Query the RAP API to get status flags for all allowed backends.

    Refer to the specification (see module docstring) for how to interpret the result.

    Raises:
        RapAPISettingsError
        RapAPICommunicationError
        RapAPIResponseError
    """
    response = _api_call(requests.get, "backend/status/")

    if response.status_code != 200:
        raise RapAPIResponseError(
            f"RAP API endpoint returned an error {response.status_code}"
        )

    return response.json()


def cancel(job_request_id, actions):
    """
    Trigger RAP API to request cancellation of specific Jobs within a Job
    Request, by action name.

    Refer to the specification (see module docstring) for how to interpret the result.

    Raises:
        RapAPISettingsError
        RapAPICommunicationError
        RapAPIResponseError
    """
    request_body = {"rap_id": job_request_id, "actions": actions}
    response = _api_call(requests.post, "rap/cancel/", request_body)

    if response.status_code != 200:
        raise RapAPIResponseError(
            f"RAP API endpoint returned an error {response.status_code}",
            body=response.json(),
        )

    return response.json()
