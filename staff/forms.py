import re

from django import forms
from django.db.models.functions import Lower
from django.utils.text import slugify

from applications.forms import YesNoField
from applications.models import Application, ResearcherRegistration
from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend, Org, Project, SiteAlert, User, Workspace


PROJECT_IDENTIFIER_PATTERN = re.compile(r"POS-20\d{2}-\d{4,}")


def user_label_from_instance(obj):
    full_name = obj.get_full_name()
    return f"{full_name} ({obj.username})" if full_name else obj.username


def normalise_project_number(number):
    number = number.strip().upper()
    if number.isdigit():
        # remove leading zeros from numeric project numbers
        number = str(int(number))
    return number


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

        slug = slugify(project_name)
        if not slug:
            raise forms.ValidationError(
                "Please use at least one letter or number in the title"
            )

        if Project.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                f'A project with the slug, "{slug}", already exists'
            )

        return project_name

    def clean_project_number(self):
        project_number = normalise_project_number(self.cleaned_data["project_number"])

        if not (
            project_number.isdigit()
            or bool(PROJECT_IDENTIFIER_PATTERN.fullmatch(project_number))
        ):
            raise forms.ValidationError(
                "Enter a numeric project number or one in the format POS-20YY-NNNN (for example, POS-2025-2001)."
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


class ProjectCreateForm(forms.ModelForm):
    """Form to create a Project."""

    class Meta:
        fields = [
            "copilot",
            "name",
            "number",
            "orgs",
        ]
        model = Project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["orgs"].queryset = Org.objects.order_by(Lower("name"))
        self.fields["copilot"].label = "Project Co-pilot"
        self.fields[
            "copilot"
        ].help_text = (
            "Ask the BI Co-pilot Lead to find out who is Co-piloting this new project."
        )

        self.fields["orgs"].label = "Link project to an organisation"
        self.fields[
            "orgs"
        ].help_text = "This is the sponsoring organisation, found in Section 9 of the NHSE OpenSAFELY Project Application form."

        self.fields["number"].label = "Project ID"
        self.fields[
            "number"
        ].help_text = "Project ID can be found in the All Projects spreadsheet."

        self.fields["name"].label = "Project title"
        self.fields[
            "name"
        ].help_text = "This can be found in Section 7 of the NHSE OpenSAFELY Project Application form."


class ProjectEditForm(forms.ModelForm):
    orgs = forms.ModelMultipleChoiceField(queryset=Org.objects.order_by(Lower("name")))

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
        model = Project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["number"].required = False

        self.fields["copilot"] = UserModelChoiceField(
            queryset=User.objects.all(), required=False
        )
        self.fields["copilot_support_ends_at"].required = False

    def clean_number(self):
        number = self.cleaned_data["number"]

        if number in (None, ""):
            return number

        number = normalise_project_number(number)

        if not (number.isdigit() or bool(PROJECT_IDENTIFIER_PATTERN.fullmatch(number))):
            raise forms.ValidationError(
                "Enter a numeric project number or one in the format POS-20YY-NNNN (for example, POS-2025-2001)."
            )

        # We have a constraint ensuring Project.number is unique (ignoring
        # nulls).  Unfortunately that fires when we save a model, giving us an
        # IntegrityError.  We have to handle this in the view if we're using a
        # plain Form, while a ModelForm will put the failure message in the form
        # instance's non_field_errors unless we manually handle the failure and
        # attach it to the number field on the form.
        #
        # Neither of these are ideal so we're also validating it here so that it
        # gets attached to the number field on forms using this mixin.
        if (
            Project.objects.exclude(pk=self.instance.pk)
            .exclude(number=None)
            .filter(number=number)
            .exists()
        ):
            raise forms.ValidationError("Project number must be unique")

        return number


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
            queryset=Project.objects.order_by("number", Lower("name")),
        )


class SiteAlertForm(forms.ModelForm):
    """Form to create or update a SiteAlert."""

    class Meta:
        model = SiteAlert
        fields = ["title", "message", "level"]
