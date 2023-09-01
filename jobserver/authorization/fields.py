import collections

from django.contrib.postgres.fields import ArrayField
from django.db import models

from .parsing import _ensure_role_paths, parse_role
from .utils import dotted_path


class RoleField(models.TextField):
    """
    Represent a single Role object as a string in the database

    This fields lets us work with role objects in the code but serialise them
    to the database as dotted python paths.
    """

    def from_db_value(self, value, expression, connection):
        """Convert dotted path to role object"""
        return parse_role(value)

    def get_prep_value(self, role):
        """Convert Role class to a dotted path for storage in the db"""
        # convert each Role to a dotted path string
        path = dotted_path(role)

        # check the path is valid
        _ensure_role_paths([path])

        return path

    def to_python(self, path):
        """Convert dotted path to role object"""
        if not path:
            return path

        if not isinstance(path, str):  # already converted
            return path

        return parse_role(path)


class RolesArrayField(ArrayField):
    """
    Represent multiple Role objects as a list in the database

    ArrayField wraps an underlying Field instances which represents each item
    in the array.  This field class sets up an ArrayField so we can avoid
    simple configuration mistakes on models and keeps the contents of the field
    unique.
    """

    def __init__(self, *args, **kwargs):
        # default to an empty list
        kwargs["default"] = list

        # we use kwargs here because migrations does the same and we want to
        # mirror that so ArrayField doesn't receive two base_field values in
        # that situation
        kwargs["base_field"] = RoleField()

        super().__init__(*args, **kwargs)

    def get_db_prep_value(self, roles, *args, **kwargs):
        # unique the roles being set in the database so a user can append roles
        # with wild abandon and we'll still have sensible data.
        roles = list(set(roles))

        # let ArrayField.get_db_prep_value() handled passing the values down to
        # the base field
        return super().get_db_prep_value(roles, *args, **kwargs)

    def get_prep_value(self, roles):
        # we want to deal with iterables here but it's valid to construct a
        # query like:
        #
        #   filter(roles__contains=MyRoleClass)
        #
        # In this case we want to wrap the value of roles in a list.
        if not isinstance(roles, collections.abc.Iterable):
            roles = [roles]

        # let RoleField handle the actual conversion
        return [self.base_field.get_prep_value(role) for role in roles]
