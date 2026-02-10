from django import forms
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.text import slugify

from applications.forms import YesNoField
from applications.models import Application, ResearcherRegistration
from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend, Org, Project, SiteAlert, User, Workspace


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


class ApplicationApproveForm(forms.Form):
    project_name = forms.CharField(help_text="Update the study name if necessary")
    project_number = forms.IntegerField()

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
        project_number = self.cleaned_data["project_number"]

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
        # add a guard to prevents KeyErrors when subclasses exclude this
        # field e.g., ProjectCreateForm.
        if "copilot_support_ends_at" in self.fields:
            self.fields["copilot_support_ends_at"].required = False

    def clean_number(self):
        number = self.cleaned_data["number"]

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


class ProjectCreateForm(forms.ModelForm):
    """Form to create a Project."""

    orgs = forms.ModelMultipleChoiceField(queryset=Org.objects.order_by(Lower("name")))

    class Meta:
        exclude = [
            "copilot_notes",
            "copilot_support_ends_at",
            "slug",
            "status_description",
            "updated_by",
        ]

        model = Project

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["copilot"] = UserModelChoiceField(
            queryset=User.objects.all(), required=True
        )

        number_field = self.fields.get("number")
        if number_field:
            number_field.required = True
            number_field.label = "Project ID"
            number_field.help_text = (
                "Project ID can be found in the All Projects spreadsheet."
            )

        name_field = self.fields.get("name")
        if name_field:
            name_field.label = "Project title"
            name_field.help_text = "This can be found in Section 7 of the NHSE OpenSAFELY Project Application form."

        orgs_field = self.fields.get("orgs")
        if orgs_field:
            orgs_field.choices = [
                ("", "Select an organisation"),
                *list(orgs_field.choices),
            ]
            orgs_field.label = "Link project to an organisation"
            orgs_field.help_text = "This is the sponsoring organisation, found in Section 9 of the NHSE OpenSAFELY Project Application form."

        status_field = self.fields.get("status")
        if status_field:
            status_field.disabled = True
            status_field.label = "Project status"
            status_field.help_text = (
                "All new projects are set to 'Ongoing' status by default"
            )

        created_at_field = self.fields.get("created_at")
        if created_at_field:
            created_at_field.disabled = True
            created_at_field.required = True
            created_at_field.label = "Project created at"
            created_at_field.initial = (
                timezone.now()
                if isinstance(created_at_field, forms.DateTimeField)
                else timezone.localdate()
            )
            created_at_field.help_text = (
                "This is automatically set to today's date, and cannot be changed."
            )

        created_by_field = self.fields.get("created_by")
        if created_by_field:
            created_by_field.disabled = True
            created_by_field.required = True
            created_by_field.label = "Project created by"
            if user is not None:
                created_by_field.initial = user.fullname
            created_by_field.help_text = "This is automatically set to the user completing the form, and cannot be changed."

    def clean_number(self):
        number = self.cleaned_data["number"]

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
