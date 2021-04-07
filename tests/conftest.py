import pytest

from jobserver.authorization.roles import SuperUser

from .factories import UserFactory


@pytest.fixture
def api_rf():
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture
def superuser():
    return UserFactory(roles=[SuperUser])
