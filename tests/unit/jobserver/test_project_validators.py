import pytest
from django.core.exceptions import ValidationError

from jobserver.project_validators import (
    check_project_identifier_format,
    normalize_project_identifier,
    validate_project_identifier,
)


def test_normalize_project_identifier():
    assert normalize_project_identifier("  pos-2025-2001  ") == "POS-2025-2001"
    assert normalize_project_identifier("") is None
    assert normalize_project_identifier(None) is None
    assert normalize_project_identifier(" 123") == "123"


def test_check_project_identifier_format():
    assert check_project_identifier_format("POS-2025-2001")
    assert check_project_identifier_format("pos-2025-2001")
    assert check_project_identifier_format("1234")
    assert check_project_identifier_format("")
    assert check_project_identifier_format(None)
    assert check_project_identifier_format(123)
    assert not check_project_identifier_format("POS2025-2001")
    assert not check_project_identifier_format("POS-20-1")


def test_validate_project_identifier():
    validate_project_identifier("1234")
    validate_project_identifier(1234)
    validate_project_identifier("pos-2025-2001")
    validate_project_identifier(None)


@pytest.mark.parametrize("value", ["POS-20-2001", "POS2025-2001", "ABC"])
def test_validate_project_identifier_rejects_invalid(value):
    with pytest.raises(ValidationError):
        validate_project_identifier(value)
