import pytest
from django.urls import reverse

from jobserver.models import Backend

from ...factories import BackendFactory, BackendMembershipFactory, UserFactory


@pytest.mark.django_db
def test_backend_no_configured_backends(monkeypatch):
    monkeypatch.setenv("BACKENDS", "")

    # backends are created by migrations
    assert Backend.objects.count() == 6


@pytest.mark.django_db
def test_backend_one_configured_backend(monkeypatch):
    monkeypatch.setenv("BACKENDS", "tpp")

    # backends are created by migrations
    assert Backend.objects.count() == 1


@pytest.mark.django_db
def test_backend_get_absolute_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_absolute_url()

    assert url == reverse("backend-detail", kwargs={"pk": backend.pk})


@pytest.mark.django_db
def test_backend_get_rotate_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_rotate_url()

    assert url == reverse("backend-rotate-token", kwargs={"pk": backend.pk})


@pytest.mark.django_db
def test_backend_rotate_token():
    backend = BackendFactory(auth_token="test")
    assert backend.auth_token == "test"

    backend.rotate_token()
    assert backend.auth_token != "test"


@pytest.mark.django_db
def test_backend_str():
    backend = BackendFactory(name="Test Backend")

    assert str(backend) == "Test Backend"


@pytest.mark.django_db
def test_backendmembership_str():
    backend = BackendFactory(display_name="Test Backend")
    user = UserFactory(username="ben")

    membership = BackendMembershipFactory(backend=backend, user=user)

    assert str(membership) == "ben | Test Backend"
