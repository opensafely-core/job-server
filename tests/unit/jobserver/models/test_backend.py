from django.urls import reverse

from jobserver.models import Backend

from ....factories import BackendFactory


def test_backend_get_edit_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_edit_url()

    assert url == reverse("staff:backend-edit", kwargs={"pk": backend.pk})


def test_backend_get_rotate_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_rotate_url()

    assert url == reverse("staff:backend-rotate-token", kwargs={"pk": backend.pk})


def test_backend_get_staff_url():
    backend = BackendFactory(auth_token="test")

    url = backend.get_staff_url()

    assert url == reverse("staff:backend-detail", kwargs={"pk": backend.pk})


def test_backend_rotate_token():
    backend = BackendFactory(auth_token="test")
    assert backend.auth_token == "test"

    backend.rotate_token()
    assert backend.auth_token != "test"


def test_backend_str():
    backend = BackendFactory(slug="test-backend")

    assert str(backend) == "test-backend"


class TestBackendManager:
    """Tests of the BackendManager()."""

    def test_only_gets_maintenance_mode_status_for_allowed_backend_slugs(self):
        """Test that we only retrieve the db maintenance status for backends contained within the allowed_slugs list"""
        tpp = BackendFactory(slug="tpp", is_in_maintenance_mode=True)
        emis = BackendFactory(slug="emis", is_in_maintenance_mode=False)
        BackendFactory(slug="other", is_in_maintenance_mode=False)

        data = Backend.objects.get_db_maintenance_mode_statuses()
        assert set(data.keys()) == {tpp.slug, emis.slug}

    def test_db_maintenance_mode_values(self):
        """Test that the correct values are retireved for backend db maintenance mode status"""
        tpp = BackendFactory(slug="tpp", is_in_maintenance_mode=True)
        emis = BackendFactory(slug="emis", is_in_maintenance_mode=False)

        data = Backend.objects.get_db_maintenance_mode_statuses()
        assert data[tpp.slug] is True
        assert data[emis.slug] is False

    def test_uses_cached_db_maintenance_statuses(self):
        """Test that cached values are used and repeated queries are avoided"""
        tpp = BackendFactory(slug="tpp", is_in_maintenance_mode=True)
        emis = BackendFactory(slug="emis", is_in_maintenance_mode=False)

        # First call to populate the cache
        first_call = Backend.objects.get_db_maintenance_mode_statuses()
        assert first_call[tpp.slug] is True
        assert first_call[emis.slug] is False

        # Simulate update to backend.is_in_maintenance_mode
        tpp.is_in_maintenance_mode = False
        tpp.save()

        # Second call to check we return the cached value, not the modified one (as the cache has a duration of 60 seconds)
        second_call = Backend.objects.get_db_maintenance_mode_statuses()
        assert second_call[tpp.slug] is True
        assert second_call[emis.slug] is False
