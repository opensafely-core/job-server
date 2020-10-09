from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import JobRequest, Workspace


class JobRequestCreateForm(forms.ModelForm):
    ALL = ("all", "All")
    BACKEND_CHOICES = [ALL] + JobRequest.BACKEND_CHOICES
    backends = forms.ChoiceField(label="Backend", choices=BACKEND_CHOICES)

    class Meta:
        fields = [
            "backends",
            "branch",
            "force_run",
            "force_run_dependencies",
            "requested_action",
            "callback_url",
        ]
        model = JobRequest
        widgets = {
            "branch": forms.TextInput(),
            "requested_action": forms.TextInput(),
            "callback_url": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    def clean_backends(self):
        """
        Validate backends selector

        Users can select one or All backends in the form, so we want to always
        give calling code a list of backends.
        """
        all_backends = [choice[0] for choice in JobRequest.BACKEND_CHOICES]

        selected = self.cleaned_data["backends"]
        if selected not in all_backends + [self.ALL[0]]:
            raise forms.ValidationError("Unknown backend", code="unknown")

        # always return a list
        if selected != self.ALL[0]:
            return [selected]

        return all_backends


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
        widgets = {
            "name": forms.TextInput(),
            "repo": forms.TextInput(),
            "branch": forms.TextInput(),
            "owner": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
