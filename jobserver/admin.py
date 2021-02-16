import django.contrib.auth.admin  # noqa: F401
import social_django.admin  # noqa: F401
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from social_django.models import Association, Nonce, UserSocialAuth

from .models import Org, Project


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


class ProjectForm(forms.ModelForm):
    class Meta:
        fields = [
            "org",
            "name",
            "display_name",
            "email",
            "project_lead",
            "proposed_start_date",
            "proposed_duration",
            "form_url",
            "has_governance_approval",
            "governance_approval_notes",
            "has_technical_approval",
            "technical_approval_notes",
        ]
        labels = {
            "org": "Organisation",
            "has_governance_approval": "Has governance approval?",
            "has_technical_approval": "Has technical approval?",
            "form_url": "Form A URL",
        }
        model = Project
        widgets = {
            "name": forms.TextInput,
            "display_name": forms.TextInput,
            "email": forms.TextInput,
            "project_lead": forms.TextInput,
            "proposed_duration": forms.TextInput,
            "form_url": forms.TextInput,
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
                    "display_name",
                    "email",
                    "project_lead",
                    "proposed_start_date",
                    "proposed_duration",
                    "form_url",
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
    ]
    list_display = [
        "pk",
        "name",
        "display_name",
        "project_lead",
        "email",
        "org",
    ]
