from django import forms

from ..utils import dotted_path
from .parsing import parse_roles


class RolesForm(forms.Form):
    """
    Base Form class for building forms with a roles Field

    The roles passed in should be a list of Role classes which get converted to
    the relevant structures for use in a template, and coverted back to Role
    classes on save.
    """

    def __init__(self, *, available_roles, **kwargs):
        super().__init__(**kwargs)

        # build choices from a list of Role classes
        choices = [(dotted_path(r), r.display_name) for r in available_roles]

        # convert initial from a list of Roles (so we can easily pass in
        # model.roles in the view) to a list of dotted paths
        initial = {}
        if "initial" in kwargs and "roles" in kwargs["initial"]:
            initial_roles = kwargs["initial"].pop("roles")
            initial = [dotted_path(r) for r in initial_roles]

        self.fields["roles"] = forms.MultipleChoiceField(
            choices=choices,
            initial=initial,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

    def clean(self):
        value = super().clean()

        if "roles" in value:
            # Replace the dotted paths with Role objects
            value["roles"] = parse_roles(value["roles"])

        return value
