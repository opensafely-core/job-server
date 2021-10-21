from django.utils.module_loading import import_string


def _ensure_role_paths(paths):
    """
    Paths must be for one of our Role Classes in jobserver.authorization.roles.
    """
    EXPECTED_PREFIX = "jobserver.authorization.roles"

    invalid_paths = [p for p in paths if not p.startswith(EXPECTED_PREFIX)]

    if not invalid_paths:
        return

    msg = f"Some Role paths did not start with {EXPECTED_PREFIX}:"
    for path in invalid_paths:
        msg += f"\n - {path}"
    raise ValueError(msg)


def parse_role(path):
    _ensure_role_paths([path])

    return import_string(path)


def parse_roles(paths):
    """Convert Role dotted paths to Role objects"""

    _ensure_role_paths(paths)

    return [parse_role(p) for p in paths]
