from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import JobRequest, User, Workspace


class JobRequestCreateForm(forms.ModelForm):
    class Meta:
        fields = [
            "force_run_dependencies",
            "will_notify",
        ]
        model = JobRequest
        widgets = {
            "will_notify": forms.RadioSelect(
                choices=[(True, "Yes"), (False, "No")],
            ),
        }

    def __init__(self, actions, *args, backends=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

        #  add action field based on the actions passed in
        choices = [(a, a) for a in actions]
        self.fields["requested_actions"] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple,
            error_messages={
                "required": "Please select at least one of the Actions listed above."
            },
        )

        if backends:
            self.fields["backend"] = forms.ChoiceField(
                choices=backends, widget=forms.RadioSelect
            )


class JobRequestSearchForm(forms.Form):
    identifier = forms.CharField()


class SettingsForm(forms.ModelForm):
    class Meta:
        fields = [
            "notifications_email",
        ]
        model = User


class WorkspaceArchiveToggleForm(forms.Form):
    is_archived = forms.BooleanField(required=False)


class WorkspaceCreateForm(forms.ModelForm):
    branch = forms.CharField(widget=forms.Select)

    class Meta:
        fields = [
            "name",
            "db",
            "repo",
            "branch",
        ]
        model = Workspace
        widgets = {
            "name": forms.TextInput(),
        }

    def __init__(self, repos_with_branches, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

        self.repos_with_branches = repos_with_branches

        choices = [(r["url"], r["name"]) for r in self.repos_with_branches]
        self.fields["repo"] = forms.ChoiceField(
            label="Repo",
            choices=choices,
            help_text="If your repo doesn't show up here, reach out to the OpenSAFELY team on Slack.",
        )

    def clean_branch(self):
        repo_url = self.cleaned_data["repo"]
        branch = self.cleaned_data["branch"]

        repo = next(
            filter(lambda r: r["url"] == repo_url, self.repos_with_branches), None
        )
        if repo is None:
            msg = "Unknown repo, please reload the page and try again"
            raise forms.ValidationError(msg)

        # normalise branch names so we can do a case insensitive match
        branches = [b.lower() for b in repo["branches"]]
        if branch.lower() not in branches:
            raise forms.ValidationError(f'Unknown branch "{branch}"')
        return branch

    def clean_name(self):
        name = self.cleaned_data["name"]

        return name.lower()


class WorkspaceNotificationsToggleForm(forms.Form):
    should_notify = forms.BooleanField(required=False)
