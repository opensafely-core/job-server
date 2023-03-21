import collections

from django.db import models

from .parsing import _ensure_role_paths, parse_roles
from .utils import dotted_path


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

        if not paths:
            return paths

        return parse_roles(paths)

    def get_prep_value(self, roles):
        """Convert Role classes to dotted paths for storage in the db"""
        if not roles:
            return super().get_prep_value(roles)

        # we want to deal with iterables here but it's valid to construct a
        # query like:
        #
        #   filter(roles__contains=MyRoleClass)
        #
        # In this case we want to wrap the value of roles in a list.
        if not isinstance(roles, collections.abc.Iterable):
            roles = [roles]

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
