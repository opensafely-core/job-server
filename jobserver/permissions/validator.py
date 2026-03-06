import re

from staff.forms import PROJECT_IDENTIFIER_PATTERN


def validate_project_identifier_in_permissions(
    project_identifiers: set[str] | dict[str, list[str]],
) -> None:
    """This function validates that a project permissions configuration
    contains valid project identifiers.

    It validates the format of the project numbers only,
    not that a project number exists in the production database.

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

        # In #5658, there's a NUMERIC_IDENTIFIER_REGEX,
        # it might be preferable to use that for consistency once merged.
        #
        # isdigit does allow leading zeros,
        # but the numeric identifier regex does too.
        # isascii is required because isdigit matches other numerals than 0-9.
        if project_identifier.isascii() and project_identifier.isdigit():
            continue

        # This is a regex matching POS-XXXX-YYYY
        if re.fullmatch(PROJECT_IDENTIFIER_PATTERN, project_identifier):
            continue

        invalid_project_identifiers.add(project_identifier)

    if invalid_project_identifiers:
        raise ValueError(
            "Invalid project identifiers found in permissions: ",
            invalid_project_identifiers,
        )
