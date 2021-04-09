import django.contrib.auth.admin  # noqa: F401
import social_django.admin  # noqa: F401
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from social_django.models import Association, Nonce, UserSocialAuth

from .models import Org, Project, User


# Remove apps we don't want in the admin
# Their admin.py files are explicitly imported above so we can unregister them
# here, otherwise they're not loaded until later as per INSTALLED_APPS
admin.site.unregister(Association)
admin.site.unregister(Group)
admin.site.unregister(Nonce)
admin.site.unregister(UserSocialAuth)


class OrgForm(forms.ModelForm):
    class Meta:
        fields = [
            "name",
        ]
        model = Org
        widgets = {
            "name": forms.TextInput,
        }


@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    form = OrgForm
    list_display = [
        "name",
        "slug",
    ]


class ProjectForm(forms.ModelForm):
    class Meta:
        fields = [
            "org",
            "name",
            "slug",
            "proposed_start_date",
            "proposed_duration",
            "next_step",
            "has_governance_approval",
            "governance_approval_notes",
            "has_technical_approval",
            "technical_approval_notes",
            "project_lead",
            "email",
            "telephone",
            "job_title",
            "team_name",
            "region",
            "purpose",
            "requested_data_meets_purpose",
            "why_data_is_required",
            "data_access_legal_basis",
            "satisfying_confidentiality",
            "ethics_approval",
            "is_research_on_cmo_priority_list",
            "funding_source",
            "team_details",
            "previous_experience_with_ehr",
            "evidence_of_scripting_languages",
            "evidence_of_sharing_in_public",
            "researcher_registrations",
            "has_signed_declaration",
        ]
        labels = {
            "org": "Organisation",
            "has_governance_approval": "Has governance approval?",
            "has_technical_approval": "Has technical approval?",
        }
        model = Project
        widgets = {
            "name": forms.TextInput,
            "proposed_duration": forms.TextInput,
            "project_lead": forms.TextInput,
            "email": forms.TextInput,
            "telephone": forms.TextInput,
            "job_title": forms.TextInput,
            "team_name": forms.TextInput,
            "region": forms.TextInput,
        }


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    fieldsets = [
        [
            None,
            {
                "fields": [
                    "org",
                    "name",
                    "proposed_start_date",
                    "proposed_duration",
                    "next_step",
                ],
            },
        ],
        [
            "Governance Approval",
            {"fields": ["governance_approval_notes", "has_governance_approval"]},
        ],
        [
            "Technical Approval",
            {"fields": ["technical_approval_notes", "has_technical_approval"]},
        ],
        [
            "Application",
            {
                "fields": [
                    "project_lead",
                    "email",
                    "telephone",
                    "job_title",
                    "team_name",
                    "region",
                    "purpose",
                    "requested_data_meets_purpose",
                    "why_data_is_required",
                    "data_access_legal_basis",
                    "satisfying_confidentiality",
                    "ethics_approval",
                    "is_research_on_cmo_priority_list",
                    "funding_source",
                    "team_details",
                    "previous_experience_with_ehr",
                    "evidence_of_scripting_languages",
                    "evidence_of_sharing_in_public",
                    "researcher_registrations",
                    "has_signed_declaration",
                ]
            },
        ],
    ]
    filter_horizontal = [
        "researcher_registrations",
    ]
    list_display = [
        "pk",
        "name",
        "project_lead",
        "email",
        "org",
        "next_step",
    ]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    exclude = [
        "password",
        "groups",
        "user_permissions",
        "roles",
    ]
    list_display = [
        "username",
        "date_joined",
        "is_approved",
    ]
    ordering = ["username"]
