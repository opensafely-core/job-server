from django import forms

from .authorization.forms import RolesForm
from .models import JobRequest, Workspace


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

    def __init__(self, actions, backends, *args, **kwargs):
        self.database_actions = kwargs.pop("database_actions")
        self.codelists_status = kwargs.pop("codelists_status")
        super().__init__(*args, **kwargs)

        #  add action field based on the actions passed in
        choices = [(a, a) for a in actions]
        self.fields["requested_actions"] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple,
            error_messages={
                "required": "Please select at least one of the Actions listed above."
            },
        )

        # only set an initial if there is one backend since the selector will
        # be hidden on the page
        initial = backends[0][0] if len(backends) == 1 else None

        # bulid the backends field based on the backends passed in
        self.fields["backend"] = forms.ChoiceField(
            choices=backends,
            initial=initial,
            widget=forms.RadioSelect,
            label="Select a backend",
        )

    def clean(self):
        super().clean()
        if self.codelists_status != "ok" and "requested_actions" in self.cleaned_data:
            requested_db_actions = [
                action
                for action in self.cleaned_data["requested_actions"]
                if action in self.database_actions
            ]
            if requested_db_actions:
                self.add_error(
                    "__all__",
                    "Some requested actions cannot be run with out-of-date codelists "
                    f"({', '.join(requested_db_actions)}). "
                    "To fix this re-run `opensafely codelists update` and commit the changes.",
                )


class EmailLoginForm(forms.Form):
    email = forms.EmailField()


class TokenLoginForm(forms.Form):
    user = forms.CharField()
    token = forms.CharField()


class RequireNameForm(forms.Form):
    name = forms.CharField()


class SettingsForm(forms.Form):
    fullname = forms.CharField()
    email = forms.EmailField()


class ProjectMembershipForm(RolesForm):
    pass


class WorkspaceArchiveToggleForm(forms.Form):
    is_archived = forms.BooleanField(required=False)


class WorkspaceCreateForm(forms.Form):
    name = forms.SlugField(
        help_text=(
            "Enter a descriptive name for the workspace, which will also "
            "be the directory name for results after job execution. Valid "
            "characters: letters, numbers, underscores, and hyphens."
        )
    )
    purpose = forms.CharField(help_text="Describe the purpose of this workspace.")
    branch = forms.CharField()

    def __init__(self, repos_with_branches, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The repo and branch fields must be dynamic as their valid values
        # depend on the state of GitHub at request-time. We construct them in
        # this function. The template JavaScript updates the branch fields when
        # repo is selected.
        self.repos_with_branches = repos_with_branches

        # Get selected repo and branch from POSTed form data, if available,
        # so we can maintain that choice in the fields that we construct.
        if self.data:
            posted_repo = self.data.get("repo")
            posted_branch = self.data.get("branch")
        else:
            posted_repo = None
            posted_branch = None

        # Find the repo data dictionary matching the POSTed name, if any.
        if self.data and "repo" in self.data:
            try:
                repo = next(
                    (r for r in self.repos_with_branches if r["url"] == posted_repo),
                )
            except StopIteration:
                raise forms.ValidationError(
                    "No matching repos found, please reload the page and try again"
                )
        else:
            repo = None

        # Construct the repo field.
        # Add a dummy invalid option to hint that the user needs to do
        # something, and prevent auto-selecting the first repo by default if
        # the user does not change the field.
        dummy_repo_choice = (None, "Please select a repo...")

        repo_choices = [dummy_repo_choice] + [
            (r["url"], r["name"]) for r in self.repos_with_branches
        ]
        self.fields["repo"] = forms.ChoiceField(
            label="Repo",
            choices=repo_choices,
            initial=repo["url"] if repo else None,
        )

        # Construct the initial branch field, to be updated dynamically by
        # JavaScript each time a different repo is selected.
        if repo:
            branch_choices = [(b, b) for b in repo["branches"]]
        else:
            # On initial GET the dummy repo option will be selected, so there
            # are no valid branches available. This prevents submitting the
            # form without changing the repo, as the clean() validates that
            # the selected repo's branch appears in self.repos_with_branches.
            branch_choices = []
        self.fields["branch"] = forms.ChoiceField(
            label="Branch",
            choices=branch_choices,
            initial=posted_branch,
        )

    def clean(self):
        cleaned_data = super().clean()
        repo_url = cleaned_data.get("repo")
        branch = cleaned_data.get("branch")

        if not (repo_url and branch):  # pragma: no cover
            return

        repo = next(
            (r for r in self.repos_with_branches if r["url"] == repo_url),
            None,
        )
        if repo is None:
            msg = "Unknown repo, please reload the page and try again"
            raise forms.ValidationError(msg)

        # normalise branch names so we can do a case insensitive match
        branches = [b.lower() for b in repo["branches"]]
        if branch.lower() not in branches:
            raise forms.ValidationError(f'Unknown branch "{branch}"')

    def clean_name(self):
        name = self.cleaned_data["name"].lower()

        if Workspace.objects.filter(name=name).exists():
            raise forms.ValidationError(
                f'A workspace with the name "{name}" already exists, please choose a unique one.'
            )

        return name


class WorkspaceEditForm(forms.Form):
    purpose = forms.CharField(help_text="Describe the purpose of this workspace.")


class WorkspaceNotificationsToggleForm(forms.Form):
    should_notify = forms.BooleanField(required=False)
