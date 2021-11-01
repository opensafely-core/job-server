from django import forms
from django.db.models.functions import Lower

from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend, Org, Project


def user_label_from_instance(obj):
    full_name = obj.get_full_name()
    return f"{obj.username} ({full_name})" if full_name else obj.username


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return user_label_from_instance(obj)


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return user_label_from_instance(obj)


class PickUsersMixin:
    """
    A generic form for picking Users to link to another object.

    We connect users to different objects (eg Orgs) via membership models.  In
    the Staff Area we want a UI to handle creating those connections.  In
    particular we want to order Users by their username, ignoring case, and
    display them with both username and full name.
    """

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)

        users = users.order_by(Lower("username"))
        self.fields["users"] = UserModelMultipleChoiceField(queryset=users)


class ApplicationApproveForm(forms.Form):
    project_name = forms.CharField(help_text="Update the study name if necessary")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orgs = Org.objects.order_by("name")

        self.fields["org"] = forms.ModelChoiceField(queryset=orgs)


class OrgAddMemberForm(PickUsersMixin, forms.Form):
    pass


class ProjectAddMemberForm(PickUsersMixin, RolesForm):
    pass


class ProjectEditForm(forms.ModelForm):
    class Meta:
        fields = [
            "name",
            "copilot",
            "uses_new_release_flow",
        ]
        model = Project

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)

        users = users.order_by(Lower("username"))
        self.fields["copilot"] = UserModelChoiceField(queryset=users)


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
