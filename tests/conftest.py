import pytest

from jobserver.github import GithubOrganizationOAuth2


@pytest.fixture
def api_rf():
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture
def dummy_backend():
    """
    Create a DummyBackend instance

    Our GithubOrganizationOAuth2 backend will be instantiated in practice.
    This allows us to test instances of it with _user_data() set (as it would
    be in practice).
    """

    class DummyBackend(GithubOrganizationOAuth2):
        def _user_data(self, *args, **kwargs):
            return {"email": "test-email", "login": "test-username"}

    return DummyBackend()
