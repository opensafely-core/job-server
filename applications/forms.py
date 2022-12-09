from django import forms

from .models import YES_NO_CHOICES, ResearcherRegistration


class PageFormBase(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # override our nullable BooleanFields since modelform_factory and thus
        # ModelForm.Meta don't let us override the field class for a field
        # which uses choices.
        radio_fields = [
            "all_applicants_completed_getting_started",
            "need_record_level_data",
            "is_approved",
        ]
        for name in radio_fields:
            if name in self.fields:
                self.fields[name] = YesNoField()


def coerce_to_bool(value):
    """
    Coerce the given value to a boolean

    Expects a boolean, or a string with the values:
        * true
        * True
        * false
        * False

    Field.has_changed() calls this function with the initial value of the field
    when testing if it has changed.  Since this is used with YesNoField this
    means initial will be a boolean value.  It also guards against unexpected
    strings since it's parsing POST data.
    """
    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        msg = f'"{value}" was of type {type(value).__name__}, expected bool or string'
        raise TypeError(msg)

    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    msg = f'Expected string value to be one of: true, True, false, or False, got "{value}"'
    raise ValueError(msg)


class YesNoField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(
            choices=YES_NO_CHOICES,
            coerce=coerce_to_bool,
            empty_value=None,
            required=False,
            widget=forms.RadioSelect,
        )


class ResearcherRegistrationPageForm(forms.ModelForm):
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
        ]
        model = ResearcherRegistration


class ResearcherRegistrationSubmissionForm(ResearcherRegistrationPageForm):
    """
    Submission form for Researchers

    When submitting an application we want to do extra validation of the
    fields, however researchers are separate to pages so we can't use the
    existing submission validation to do that.  Instead we take the form used
    to create/edit researchers and add cross-field validation to it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["does_researcher_need_server_access"].required = True
        self.fields["has_taken_safe_researcher_training"].required = True

    def clean(self):
        cleaned_data = super().clean()

        # require number and phone type if the user is going to need server
        # access.
        does_researcher_need_server_access = cleaned_data.get(
            "does_researcher_need_server_access", False
        )
        telephone = cleaned_data["telephone"]
        phone_type = cleaned_data.get("phone_type", None)
        if does_researcher_need_server_access:
            if not telephone:
                msg = "A phone number is required to access the results server."
                self.add_error("telephone", msg)

            if not phone_type:
                msg = "A phone type is required to access the results server."
                self.add_error("phone_type", msg)

        # require training org and pass date when researcher has taken safe
        # researcher training.
        has_taken_safe_researcher_training = cleaned_data.get(
            "has_taken_safe_researcher_training", False
        )
        training_with_org = cleaned_data["training_with_org"]
        training_passed_at = cleaned_data["training_passed_at"]
        if has_taken_safe_researcher_training:
            if not training_with_org:
                msg = (
                    "When a researcher has undertaken safe researcher training we "
                    "need to know the organisation they completed it with."
                )
                self.add_error("training_with_org", msg)

            if not training_passed_at:
                msg = (
                    "When a researcher has undertaken safe researcher training we "
                    "need to know the date they passed the course."
                )
                self.add_error("training_passed_at", msg)
