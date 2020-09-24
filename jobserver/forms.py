from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .api.models import Workspace


class WorkspaceCreateForm(forms.ModelForm):
    class Meta:

        fields = [
            "name",
            "repo",
            "branch",
            "owner",
            "db",
        ]
        model = Workspace

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
