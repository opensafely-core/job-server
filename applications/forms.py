from django import forms

from .models import Application


class Form1(forms.ModelForm):
    class Meta:
        fields = [
            "full_name",
            "email",
            "telephone",
            "job_title",
            "team_name",
            "organisation",
        ]
        model = Application


class Form2(forms.ModelForm):
    class Meta:
        fields = [
            "study_name",
            "purpose",
        ]
        model = Application


class Form3(forms.ModelForm):
    class Meta:
        fields = [
            "purpose",
            "author_name",
            "author_email",
            "author_organisation",
        ]
        model = Application


class Form4(forms.ModelForm):
    class Meta:
        fields = [
            "study_data",
            "need_record_level_data",
        ]
        model = Application


class Form5(forms.ModelForm):
    class Meta:
        fields = [
            "record_level_data_reasons",
        ]
        model = Application


class Form6(forms.ModelForm):
    class Meta:
        fields = [
            "is_study_research",
            "is_study_a_service_evaluation",
        ]
        model = Application


class Form7(forms.ModelForm):
    class Meta:
        fields = [
            "hra_ires_id",
            "hra_rec_reference",
            "institutional_rec_reference",
        ]
        model = Application


class Form8(forms.ModelForm):
    class Meta:
        fields = [
            "institutional_rec_reference",
        ]
        model = Application


class Form9(forms.ModelForm):
    class Meta:
        fields = [
            "is_on_cmo_priority_list",
        ]
        model = Application


class Form10(forms.ModelForm):
    class Meta:
        fields = [
            "funding_details",
        ]
        model = Application


class Form11(forms.ModelForm):
    class Meta:
        fields = [
            "team_details",
        ]
        model = Application


class Form12(forms.ModelForm):
    class Meta:
        fields = [
            "previous_experience_with_ehr",
        ]
        model = Application


class Form13(forms.ModelForm):
    class Meta:
        fields = [
            "evidence_of_coding",
        ]
        model = Application


class Form14(forms.ModelForm):
    class Meta:
        fields = [
            "evidence_of_sharing_in_public_domain_before",
        ]
        model = Application


class Form15(forms.ModelForm):
    class Meta:
        fields = [
            "number_of_researchers_needing_access",
        ]
        model = Application


class Form16(forms.ModelForm):
    class Meta:
        fields = [
            "has_agreed_to_terms",
        ]
        model = Application
