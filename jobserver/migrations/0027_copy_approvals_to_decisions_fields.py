# Generated by Django 4.1.7 on 2023-05-02 15:21

from django.db import migrations
from django.db.models import F


def copy_approved_to_decision_fields(apps, schema_editor):
    ReportPublishRequest = apps.get_model("jobserver", "ReportPublishRequest")
    ReleaseFilePublishRequest = apps.get_model("jobserver", "ReleaseFilePublishRequest")

    ReportPublishRequest.objects.exclude(approved_at=None).update(
        decision_at=F("approved_at"),
        decision_by=F("approved_by"),
        decision="approved",
    )
    ReleaseFilePublishRequest.objects.exclude(approved_at=None).update(
        decision_at=F("approved_at"),
        decision_by=F("approved_by"),
        decision="approved",
    )


def wipe_decision_fields(apps, schema_editor):
    ReportPublishRequest = apps.get_model("jobserver", "ReportPublishRequest")
    ReleaseFilePublishRequest = apps.get_model("jobserver", "ReleaseFilePublishRequest")

    ReportPublishRequest.objects.update(
        decision_at=None, decision_by=None, decision=None
    )
    ReleaseFilePublishRequest.objects.update(
        decision_at=None, decision_by=None, decision=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0026_add_decision_fields_to_publish_requests"),
    ]

    operations = [
        migrations.RunPython(
            copy_approved_to_decision_fields, reverse_code=wipe_decision_fields
        )
    ]