import pytest

from jobserver.permissions.validator import validate_project_identifier_in_permissions


# We use the identifiers also as names in the tests.
# Therefore, they need to be in an ordered data structure,
# to ensure they are consistent across xdist workers.
project_identifier_test_cases = [
    # project_identifiers, expected_invalid
    # Empty
    ([], []),
    # Single slug exception
    (["opensafely-internal"], []),
    # Simple allowed number cases.
    (["123"], []),
    (["3"], []),
    (["30"], []),
    (["300"], []),
    (["3000"], []),
    # Leading zero currently permitted.
    (["03"], []),
    # Simple disallowed number cases.
    (["-123"], ["-123"]),
    (["1.0"], ["1.0"]),
    # POS identifiers allowed.
    (["POS-2026-9999"], []),
    (["POS-2025-0001"], []),
    (["POS-2024-0001"], []),
    (["POS-2024-9999"], []),
    # Handling of duplicates.
    (["POS-2026-9999", "POS-2026-9999"], []),
    (["POS-2026-9999", "my_project", "my_project"], ["my_project"]),
    # TODO: are five digit numbers really allowed?
    # They currently are by the regex.
    (["POS-2024-10000"], []),
    # Other non-matching POS strings.
    (["POS-"], ["POS-"]),
    (["POS-2025"], ["POS-2025"]),
    (["POS-2025-"], ["POS-2025-"]),
    (["POS-2025-0"], ["POS-2025-0"]),
    (["POS-3000-0001"], ["POS-3000-0001"]),
    (["POS-123-5678"], ["POS-123-5678"]),
    (["POS-1234-ABCD"], ["POS-1234-ABCD"]),
    (["POS-ABCD-1234"], ["POS-ABCD-1234"]),
    (["pos-2025-0001"], ["pos-2025-0001"]),
    # Miscellaneous strings disallowed.
    ([""], [""]),
    (["ABC"], ["ABC"]),
    (["my_project"], ["my_project"]),
    (["another_slug"], ["another_slug"]),
    (["$invalid"], ["$invalid"]),
    (["!$"], ["!$"]),
    # Multiple entries allowed.
    (["123", "POS-2026-0002"], []),
    (["123", "POS-2026-0002", "POS-2025-0001"], []),
    (["123", "POS-2026-0002", "POS-2025-0001", "456"], []),
    # Multiple entries disallowed.
    (["A123", "POS-2026-0002"], ["A123"]),
    (["A123", "POS-2026-000", "POS-2025-0001"], ["A123", "POS-2026-000"]),
    (["A123", "POS-2026-000", "!"], ["A123", "POS-2026-000", "!"]),
    # Check behaviour with a few dicts.
    # In practice, we're only iterating through the keys,
    # so the behaviour should be as the lists.
    # Ideally, we specify permissions with a single type.
    # An empty dict is allowed.
    (dict(), []),
    ({"POS-2026-0001": ["icnarc", "appointments"]}, []),
    ({"opensafely-internal": ["sgss_covid_all_tests"]}, []),
    ({"123": ["icnarc", "ukrr"]}, []),
    # Note: A dict with an empty list works,
    # because we're not currently validating the list value,
    # only the identifier.
    ({"POS-2026-0001": []}, []),
    ({"my_project": ["icnarc", "appointments"]}, ["my_project"]),
    (
        {
            "my_project": ["icnarc", "appointments"],
            "POS-2026-0001": ["sgss_covid_all_tests"],
        },
        ["my_project"],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-0001": ["sgss_covid_all_tests"],
        },
        [],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-0001": ["icnarc", "sgss_covid_all_tests"],
            "123": ["ukrr"],
        },
        [],
    ),
    (
        {
            "opensafely-internal": ["icnarc", "appointments"],
            "POS-2026-0001": ["icnarc", "sgss_covid_all_tests"],
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
    project_identifiers, expected_invalid
):
    identifiers = set(project_identifiers)

    if not expected_invalid:
        validate_project_identifier_in_permissions(identifiers)
    else:
        with pytest.raises(ValueError) as exc:
            validate_project_identifier_in_permissions(identifiers)

        assert set(expected_invalid) == exc.value.args[1]
