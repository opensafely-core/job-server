from django.db import models

from .parsing import _ensure_role_paths, parse_roles
from .utils import dotted_path


class ExtractRoles(models.Func):
    """
    Extract a roles field into a CharField

    When querying models using a Role we need to deal with the underlying
    JSONField, which on SQLite doesn't support Django's __contains expression.
    However, Django's .alias() allows us to create an expression which we can
    filter on later.

    This function uses SQLite's json_extract function to pull the value of a
    given field into a CharField which does support __contains.  For example
    querying for Users with the CoreDeveloper role in SQL looks like this:

        SELECT *
         FROM jobserver_user
        WHERE json_extract(roles, '$')
         LIKE '%jobserver.authorization.roles.CoreDeveloper%';

    To replicate this query via the ORM one can use it like this:

        User.objects.alias(extracted=ExtractRoles("roles")).filter(
            extracted__contains="CoreDeveloper"
        )
    """

    function = "json_extract"
    template = "%(function)s(%(expressions)s, '$')"
    output_field = models.CharField()


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
                models = "\n".join(f"   - {model}" for model in role.models)
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
