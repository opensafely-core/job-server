import re

from staff.forms import PROJECT_IDENTIFIER_PATTERN


# In #5658, there's a NUMERIC_IDENTIFIER_REGEX,
# it might be preferable to use that for consistency once merged.
NUMERIC_IDENTIFIER_REGEX = re.compile(r"^[0-9]+$")


def validate_project_identifier_in_permissions(
    project_identifiers: set[str] | dict[str, list[str]],
) -> None:
    """This function validates that a project permissions configuration
    contains valid project identifiers.

    It validates the format of the project numbers only,
    not that a project number exists in the production database.

    It also does not validate values provided for a project identifier,
    such as allowed ehrQL tables.

    Project numbers in these configurations are strings and can be:

    * project slugs
    * entirely numeric identifiers
    * identifiers of the format `POS-XXXX-YYYY` where X is a year, and Y
      is a number with 4 digits or more.

    In practice, active projects should have an identifier, and not fall
    back to project slugs. The one exception is the opensafely-internal project,
    and this should get assigned a project number in future.
    """
    invalid_project_identifiers = set()

    for project_identifier in project_identifiers:
        # This is a specific exemption for the one case
        # where a project slug is used.
        # We should remove this in future and use a standard identifier.
        if project_identifier == "opensafely-internal":
            continue

        if NUMERIC_IDENTIFIER_REGEX.fullmatch(project_identifier):
            continue

        if PROJECT_IDENTIFIER_PATTERN.fullmatch(project_identifier):
            continue

        invalid_project_identifiers.add(project_identifier)

    if invalid_project_identifiers:
        raise ValueError(
            "Invalid project identifiers found in permissions: ",
            invalid_project_identifiers,
        )
