import pytest
import structlog
from structlog.testing import LogCapture

from jobserver.authorization.roles import SuperUser

from .factories import UserFactory


@pytest.fixture
def api_rf():
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


@pytest.fixture
def superuser():
    return UserFactory(roles=[SuperUser])
