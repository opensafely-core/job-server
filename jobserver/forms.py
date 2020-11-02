from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import JobRequest, Workspace


class JobRequestCreateForm(forms.ModelForm):
    class Meta:
        fields = [
            "force_run",
            "force_run_dependencies",
        ]
        model = JobRequest

    def __init__(self, actions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

        #  add action field based on the actions passed in
        choices = [(a, a) for a in actions]
        self.fields["requested_actions"] = forms.MultipleChoiceField(
            choices=choices, widget=forms.CheckboxSelectMultiple
        )


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
        self.fields["repo"] = forms.ChoiceField(label="Repo", choices=choices)

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
