from collections.abc import Iterable

from jobserver.models.project import NUMBER_REGEX


def validate_project_identifier_in_permissions(
    project_identifiers: Iterable[str],
) -> None:
    """This function validates that a project permissions configuration
    contains valid project identifiers.

    This function:

    * validates the format of the project identifiers only,
      not that a project identifier exists in the production database.
    * does not validate associated values provided in the permissions
      for that identifier, such as ehrQL tables a project can access

    Project identifiers in these configurations are strings, but
    currently referred to as "numbers".

    These are almost always identifiers matched by the imported
    regex. Refer to that defintion for details.
    The one exception is the opensafely-internal project,
    and this project should get assigned an identifier in future.
    """
    invalid_project_identifiers = {
        project_identifier
        for project_identifier in project_identifiers
        if not NUMBER_REGEX.fullmatch(project_identifier)
        # This is a specific exemption for the one case
        # where a project slug is used.
        # We should remove this in future and use a standard identifier.
        and project_identifier != "opensafely-internal"
    }

    if invalid_project_identifiers:
        raise ValueError(
            "Invalid project identifiers found in permissions: ",
            invalid_project_identifiers,
        )
