from django.db import models
from django.utils.module_loading import import_string


def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"


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


def parse_roles(paths):
    """Convert Role dotted paths to Role objects"""

    _ensure_role_paths(paths)

    return [import_string(p) for p in paths]


class RolesField(models.JSONField):
    """
    Custom Model Field to link our Role classes to a Model

    Our Roles are implemented as classes so we store them in the database as
    dotted path strings to those classes.  This field handles converting to and
    from the dotted path strings, and ensures roles are unique.
    """

    description = "A list of Roles"

    def __init__(self, *args, **kwargs):
        kwargs["default"] = list
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        paths = super().from_db_value(value, expression, connection)

        if paths is None:
            return paths

        return parse_roles(paths)

    def get_prep_value(self, roles):
        """Convert Role classes to dotted paths for storage in the db"""
        if not roles:
            return super().get_prep_value(roles)

        # check each Role is valid for the calling class
        invalid_roles = []
        for role in roles:
            # compare by dotted path because isinstance(self.model,
            # apps.get_model(role.model)) doesn't work and I can't see why
            if dotted_path(self.model) not in role.models:
                invalid_roles.append(role)

        if invalid_roles:
            msg = f"Some roles could not be assigned to {self.model.__name__}"

            for role in invalid_roles:
                models = "\n".join([f"   - {model}" for model in role.models])
                msg += f"\n - {role.__name__} can only be assigned to these models:\n{models}"

            raise ValueError(msg)

        # convert each Role to a dotted path string
        paths = {dotted_path(r) for r in roles}
        paths = list(paths)

        _ensure_role_paths(paths)

        return super().get_prep_value(paths)

    def to_python(self, paths):
        if not paths:
            return paths

        if not isinstance(paths[0], str):  # already converted
            return paths

        return parse_roles(paths)
