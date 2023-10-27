import pytest

from interactive.opencodelists import OpenCodelistsAPI

from ..fakes import FakeOpenCodelistsAPI
from .utils import compare


pytestmark = [
    pytest.mark.verification,
]


@pytest.fixture
def opencodelists_api():
    """create a new API instance for these tests"""
    return OpenCodelistsAPI()


def test_get_codelists(enable_network, opencodelists_api):
    args = ["snomedct"]

    real = opencodelists_api.get_codelists(*args)
    fake = FakeOpenCodelistsAPI().get_codelists(*args)

    compare(fake, real)

    assert real is not None


def test_get_codelists_with_unknown_coding_system(enable_network, opencodelists_api):
    args = ["test"]

    real = opencodelists_api.get_codelists(*args)
    fake = FakeOpenCodelistsAPI().get_codelists(*args)

    compare(fake, real)

    assert real == []


def test_check_codelists(enable_network, opencodelists_api):
    args = ["{}", ""]

    real = opencodelists_api.check_codelists(*args)
    fake = FakeOpenCodelistsAPI().check_codelists(*args)

    compare(fake, real)
