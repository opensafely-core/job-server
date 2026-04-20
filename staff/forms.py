from django import forms
from django.db.models.functions import Lower
from django.utils.text import slugify

from applications.forms import YesNoField
from applications.models import Application, ResearcherRegistration
from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend, Org, Project, SiteAlert, User, Workspace
from jobserver.models.project import NUMBER_REGEX, POS_FORMAT_REGEX


def user_label_from_instance(obj):
    full_name = obj.get_full_name()
    return f"{full_name} ({obj.username})" if full_name else obj.username


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

        self.fields["users"] = UserModelMultipleChoiceField(queryset=users)


def _validate_slug(project_name: str):
    """Validate that a project name slugifies to non-empty, and does not
    already exist."""
    slug = slugify(project_name)
    if not slug:
        message = "Please enter at least one letter or number. "
        raise forms.ValidationError(message)

    if Project.objects.filter(slug=slug).exists():
        raise forms.ValidationError(
            f'Project with the URL slug "{slug}" generated '
            "from this project title already exists."
        )


class ApplicationApproveForm(forms.Form):
    project_name = forms.CharField(help_text="Update the study name if necessary")
    project_number = forms.CharField()

    def __init__(self, orgs, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["org"] = forms.ChoiceField(choices=[(o.pk, o.name) for o in orgs])

    def clean_org(self):
        return Org.objects.get(pk=self.cleaned_data["org"])

    def clean_project_name(self):
        project_name = self.cleaned_data["project_name"]

        if Project.objects.filter(name=project_name).exists():
            raise forms.ValidationError(f'Project "{project_name}" already exists.')

        _validate_slug(project_name)

        return project_name

    def clean_project_number(self):
        project_number = self.cleaned_data["project_number"]
        if not NUMBER_REGEX.fullmatch(project_number):
            raise forms.ValidationError(
                "Enter a whole number or use the format POS-20YY-NNNN (for example, POS-2026-2001)."
            )

        if Project.objects.filter(number=project_number).exists():
            raise forms.ValidationError(
                f'Project with number "{project_number}" already exists.'
            )

        return project_number


class OrgAddGitHubOrgForm(forms.Form):
    name = forms.CharField()


class OrgAddMemberForm(PickUsersMixin, forms.Form):
    pass


class ProjectAddMemberForm(PickUsersMixin, RolesForm):
    pass


class UniqueProjectNumberMixin:
    """Mixin to validate Project.number uniqueness in the form, not the model."""

    def clean_number(self):
        # The model uniqueness constraint triggers when the form is saved but
        # the resulting error is not attached to the form field. Raise a
        # ValidationError here instead, attaching it and improving the UI.
        number = self.cleaned_data["number"]
        if number in (None, ""):
            return number

        if Project.objects.exclude(pk=self.instance.pk).filter(number=number).exists():
            raise forms.ValidationError("Project with this Project ID already exists.")
        return number


class ProjectCreateForm(forms.ModelForm, UniqueProjectNumberMixin):
    """Form to create a Project."""

    class Meta:
        fields = [
            "copilot",
            "name",
            "number",
            "orgs",
        ]
        model = Project
        field_classes = {
            # orgs is a ManyToManyField, but we only want to allow one to be selected.
            # Override the default field ModelForm gives (ModelMultipleChoiceField).
            "orgs": forms.models.ModelChoiceField,
            "copilot": UserModelChoiceField,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["orgs"].queryset = Org.objects.order_by(Lower("name"))
        self.fields["copilot"].required = False
        self.fields["copilot"].queryset = User.objects.potential_copilots()

    def clean_name(self):
        _validate_slug(self.cleaned_data["name"])
        return self.cleaned_data["name"]

    def clean(self):
        # Only require copilot be set for projects with a POS-format project number.
        # TODO: When we implement project category, the second part of the
        # condition could use that.
        if (
            "copilot" not in self.cleaned_data or not self.cleaned_data["copilot"]
        ) and POS_FORMAT_REGEX.fullmatch(self.cleaned_data["number"]):
            self.add_error(
                "copilot",
                forms.ValidationError(
                    "The copilot field is required for projects with a 'POS-' "
                    "project number."
                ),
            )


class ProjectEditForm(forms.ModelForm, UniqueProjectNumberMixin):
    class Meta:
        fields = [
            "copilot",
            "copilot_notes",
            "copilot_support_ends_at",
            "name",
            "number",
            "orgs",
            "slug",
            "status",
            "status_description",
        ]
        field_classes = {
            "copilot": UserModelChoiceField,
        }
        model = Project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["orgs"].queryset = Org.objects.order_by(Lower("name"))
        self.fields["copilot"].required = False
        self.fields["copilot"].queryset = User.objects.potential_copilots()


class ProjectLinkApplicationForm(forms.Form):
    application = forms.CharField()

    def __init__(self, instance, *args, **kwargs):
        # this is used by a subclass of UpdateView, which expects a ModelForm,
        # so all we're doing here is dropping the `instance` arg.
        super().__init__(*args, **kwargs)

    def clean_application(self):
        pk = self.cleaned_data["application"]

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            raise forms.ValidationError("Unknown Application")

        if application.project:
            raise forms.ValidationError("Can't link Application to multiple Projects")

        return application


class ProjectMembershipForm(RolesForm):
    pass


class ResearcherRegistrationEditForm(forms.ModelForm):
    does_researcher_need_server_access = YesNoField()
    has_taken_safe_researcher_training = YesNoField()
    phone_type = forms.TypedChoiceField(
        choices=ResearcherRegistration.PhoneTypes.choices,
        empty_value=None,
        required=False,
        widget=forms.RadioSelect,
    )

    class Meta:
        fields = [
            "name",
            "job_title",
            "email",
            "does_researcher_need_server_access",
            "telephone",
            "phone_type",
            "has_taken_safe_researcher_training",
            "training_with_org",
            "training_passed_at",
            "daa",
            "github_username",
        ]
        model = ResearcherRegistration


class UserForm(forms.Form):
    fullname = forms.CharField(required=False)

    def __init__(self, *, available_backends, **kwargs):
        fullname = kwargs.pop("fullname")

        super().__init__(**kwargs)

        # build choices from the available backends
        choices = backends_to_choices(available_backends)

        self.fields["backends"] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )
        self.fields["fullname"].initial = fullname

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


class WorkspaceModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.title


class WorkspaceEditForm(forms.ModelForm):
    purpose = forms.CharField(required=False)

    class Meta:
        fields = [
            "project",
            "is_archived",
            "purpose",
        ]
        model = Workspace

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["project"] = WorkspaceModelChoiceField(
            queryset=Project.objects.all().order_by_project_identifier()
        )


class SiteAlertForm(forms.ModelForm):
    """Form to create or update a SiteAlert."""

    class Meta:
        model = SiteAlert
        fields = ["title", "message", "level"]
