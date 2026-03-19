import pytest

from jobserver.permissions import validator


class StubRegexPattern:
    """StubRegexPattern stubs the regex in the validation function.

    The regex used is already tested elsewhere in the codebase."""

    def fullmatch(self, value):
        return (
            True
            if value
            in {
                "123",
                "456",
                "POS-2026-1001",
                "POS-2026-1002",
            }
            else False
        )


# We use the identifiers also as names in the tests.
# Therefore, they need to be in an ordered data structure,
# to ensure they are consistent across xdist workers.
project_identifier_test_cases = [
    # project_identifiers, expected_invalid
    # Empty
    ([], []),
    # Single slug exception.
    (["opensafely-internal"], []),
    # Handling of duplicates.
    (["POS-2026-1001", "POS-2026-1001"], []),
    (["POS-2026-1001", "my_project", "my_project"], ["my_project"]),
    # Multiple entries allowed.
    (["123", "POS-2026-1001"], []),
    (["123", "POS-2026-1001", "POS-2026-1002"], []),
    (["123", "POS-2026-1001", "POS-2026-1002", "456"], []),
    # Multiple entries disallowed.
    (["A123", "POS-2026-1002"], ["A123"]),
    (["A123", "POS-2026-000", "POS-2026-1001"], ["A123", "POS-2026-000"]),
    (["A123", "POS-2026-000", "!"], ["A123", "POS-2026-000", "!"]),
    # Check behaviour with a few dicts
    # since we do have dicts in the current code.
    # In practice, we're only iterating through the keys,
    # so the behaviour should be as the lists.
    # An empty dict is allowed.
    (
        dict(),
        [],
    ),
    (
        {
            "POS-2026-1001": ["icnarc", "appointments"],
        },
        [],
    ),
    (
        {
            "opensafely-internal": ["sgss_covid_all_tests"],
        },
        [],
    ),
    (
        {
            "123": ["icnarc", "ukrr"],
        },
        [],
    ),
    # Note: A dict with an empty list works,
    # because we're not currently validating the list value,
    # only the identifier.
    (
        {
            "POS-2026-1001": [],
        },
        [],
    ),
    (
        {
            "my_project": ["icnarc", "appointments"],
        },
        ["my_project"],
    ),
    (
        {
            "my_project": ["icnarc", "appointments"],
            "POS-2026-1001": ["sgss_covid_all_tests"],
        },
        ["my_project"],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-1001": ["sgss_covid_all_tests"],
        },
        [],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-1001": ["icnarc", "sgss_covid_all_tests"],
            "123": ["ukrr"],
        },
        [],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-1001": ["icnarc", "sgss_covid_all_tests"],
            "123": ["ukrr"],
            "invalid-slug": ["ukrr"],
        },
        ["invalid-slug"],
    ),
]


@pytest.mark.parametrize(
    "project_identifiers,expected_invalid",
    project_identifier_test_cases,
    ids=[
        repr(project_identifiers)
        for project_identifiers, _ in project_identifier_test_cases
    ],
)
def test_validate_project_identifier_in_permissions(
    project_identifiers, expected_invalid, mocker
):
    mocker.patch.object(validator, "NUMBER_REGEX", StubRegexPattern())
    identifiers = set(project_identifiers)

    if not expected_invalid:
        validator.validate_project_identifier_in_permissions(identifiers)
    else:
        with pytest.raises(ValueError) as exc:
            validator.validate_project_identifier_in_permissions(identifiers)

        assert set(expected_invalid) == exc.value.args[1]
