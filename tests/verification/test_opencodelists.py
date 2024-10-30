import pytest

from jobserver.opencodelists import OpenCodelistsAPI

from ..fakes import FakeOpenCodelistsAPI
from .utils import assert_deep_type_equality, assert_public_method_signature_equality


pytestmark = [pytest.mark.verification, pytest.mark.disable_db]


@pytest.fixture
def opencodelists_api():
    """create a new API instance for these tests"""
    return OpenCodelistsAPI()


def test_fake_public_method_signatures():
    """Test that `FakeOpenCodelistsAPI` has the same public methods with the
    same signatures as the real one."""
    assert_public_method_signature_equality(
        OpenCodelistsAPI,
        FakeOpenCodelistsAPI,
    )


def test_get_codelists(enable_network, opencodelists_api):
    args = ["snomedct"]

    real = opencodelists_api.get_codelists(*args)
    fake = FakeOpenCodelistsAPI().get_codelists(*args)

    assert_deep_type_equality(fake, real)

    assert real is not None


def test_get_codelists_with_unknown_coding_system(enable_network, opencodelists_api):
    args = ["test"]

    real = opencodelists_api.get_codelists(*args)
    fake = FakeOpenCodelistsAPI().get_codelists(*args)

    assert_deep_type_equality(fake, real)

    assert real == []


def test_check_codelists(enable_network, opencodelists_api):
    args = ["{}", ""]

    real = opencodelists_api.check_codelists(*args)
    fake = FakeOpenCodelistsAPI().check_codelists(*args)

    assert_deep_type_equality(fake, real)
