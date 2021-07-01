import pytest
from rest_framework.exceptions import NotAuthenticated

from jobserver.api import get_backend_from_token
from jobserver.models import Backend


def test_token_backend_empty_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token(None)


def test_token_backend_no_token():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("")


@pytest.mark.django_db
def test_token_backend_success(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    tpp = Backend.objects.get(name="tpp")

    assert get_backend_from_token(tpp.auth_token) == tpp


@pytest.mark.django_db
def test_token_backend_unknown_backend():
    with pytest.raises(NotAuthenticated):
        get_backend_from_token("test")
