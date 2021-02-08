from django import forms
from django.contrib import admin

from .models import Org, Project


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
            "email",
            "project_lead",
            "proposed_start_date",
            "proposed_duration",
            "has_governance_approval",
            "has_technical_approval",
        ]
        labels = {
            "org": "Organisation",
        }
        model = Project
        widgets = {
            "name": forms.TextInput,
            "email": forms.TextInput,
            "project_lead": forms.TextInput,
            "proposed_duration": forms.TextInput,
        }


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
