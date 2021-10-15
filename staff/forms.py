from django import forms

from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend


class AddMemberForm(forms.Form):
    """
    A generic form for adding Members to another object.

    We connect users to different objects (eg Orgs) via membership models.  In
    the Staff Area we want a UI to handle creating those connections.
    """

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["users"] = forms.MultipleChoiceField(
            choices=list(self.build_user_choices(users)),
        )

    def build_user_choices(self, users):
        for user in users:
            full_name = user.get_full_name()
            label = f"{user.username} ({full_name})" if full_name else user.username

            yield user.pk, label


class ProjectAddMemberForm(RolesForm, AddMemberForm):
    pass


class UserForm(RolesForm):
    is_superuser = forms.BooleanField(required=False)

    def __init__(self, *, available_backends, **kwargs):
        super().__init__(**kwargs)

        # build choices from the available backends
        choices = backends_to_choices(available_backends)

        self.fields["backends"] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

    def clean_backends(self):
        """Convert backend names to Backend instances"""
        return Backend.objects.filter(slug__in=self.cleaned_data["backends"])


class UserOrgsForm(forms.Form):
    def __init__(self, *, available_orgs, **kwargs):
        super().__init__(**kwargs)

        # build choices from the available orgs
        # choices = backends_to_choices(available_orgs)

        self.fields["orgs"] = forms.ModelMultipleChoiceField(
            # choices=choices,
            queryset=available_orgs,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )
