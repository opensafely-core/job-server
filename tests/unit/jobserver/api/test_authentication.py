import pytest
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from jobserver.api.authentication import NoAuthentication, get_backend_from_token

from ....factories import BackendFactory


def test_noauthentication_permission_denied(api_rf):
    request = api_rf.get("/")

    with pytest.raises(PermissionDenied):
        NoAuthentication().authenticate(request)


def test_token_backend_empty_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token(None)


def test_token_backend_no_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("")


def test_token_backend_success():
    backend = BackendFactory(slug="tpp")

    assert get_backend_from_token(backend.auth_token) == backend


def test_token_backend_unknown_backend():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("test")
