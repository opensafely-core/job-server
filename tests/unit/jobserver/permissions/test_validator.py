import pytest

from jobserver.permissions.validator import validate_project_identifier_in_permissions


# We use the identifiers also as names in the tests.
# Therefore, they need to be ordered,
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
]


@pytest.mark.parametrize(
    "project_identifiers,expected_invalid",
    project_identifier_test_cases,
    ids=[
        "empty" if not identifiers else ",".join(identifiers)
        for identifiers, _ in project_identifier_test_cases
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
