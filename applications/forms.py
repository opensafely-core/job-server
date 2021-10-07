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
            "is_on_cmo_priority_list",
            "is_approved",
        ]
        for name in radio_fields:
            if name in self.fields:
                self.fields[name] = YesNoField()


class YesNoField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(
            choices=YES_NO_CHOICES,
            coerce=lambda x: x == "True",
            empty_value=None,
            required=False,
            widget=forms.RadioSelect,
        )


class ResearcherRegistrationForm(forms.ModelForm):
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
