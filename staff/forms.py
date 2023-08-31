from django import forms
from django.db.models.functions import Lower
from django.utils.text import slugify

from applications.forms import YesNoField
from applications.models import Application, ResearcherRegistration
from jobserver.authorization.forms import RolesForm
from jobserver.backends import backends_to_choices
from jobserver.models import Backend, Org, Project, User, Workspace


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

        users = users.order_by(Lower("username"))
        self.fields["users"] = UserModelMultipleChoiceField(queryset=users)


class ApplicationApproveForm(forms.Form):
    org = forms.ModelChoiceField(queryset=Org.objects.order_by("name"))
    project_name = forms.CharField(help_text="Update the study name if necessary")
    project_number = forms.IntegerField()

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


class ProjectCreateForm(forms.Form):
    application_url = forms.URLField()
    copilot = UserModelChoiceField(
        queryset=User.objects.order_by(Lower("fullname"), "username")
    )
    name = forms.CharField()
    number = forms.IntegerField()
    org = forms.ModelChoiceField(queryset=Org.objects.order_by("name"))

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
        #
        # We can't abstract this with ProjectEditForm since we have no Project
        # instance to exclude here.
        if Project.objects.exclude(number=None).filter(number=number).exists():
            raise forms.ValidationError("Project number must be unique")

        return number


class ProjectEditForm(forms.ModelForm):
    class Meta:
        fields = [
            "application_url",
            "copilot",
            "copilot_notes",
            "copilot_support_ends_at",
            "name",
            "number",
            "org",
            "slug",
            "status",
            "status_description",
        ]
        model = Project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["application_url"].required = False
        self.fields["number"].required = False

        self.fields["copilot"] = UserModelChoiceField(
            queryset=User.objects.order_by(Lower("username")), required=False
        )
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
        #
        # We can't abstract this with ProjectCreateForm since we have to filter
        # out the current Project instance here too.
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


class UserCreateForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.filter(workspaces__name__endswith="interactive")
        .distinct()
        .order_by(Lower("org__name"), Lower("name"))
    )
    name = forms.CharField()
    email = forms.EmailField()


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
    class Meta:
        fields = [
            "project",
            "is_archived",
        ]
        model = Workspace

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["project"] = WorkspaceModelChoiceField(
            queryset=Project.objects.order_by("number", Lower("name")),
        )
