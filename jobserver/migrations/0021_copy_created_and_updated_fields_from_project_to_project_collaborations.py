# Generated by Django 5.0.1 on 2024-01-18 10:14

from django.db import migrations


def copy_created_and_updated_fields_from_project_to_collaboration(apps, schema_editor):
    ProjectCollaboration = apps.get_model("jobserver", "ProjectCollaboration")

    for collaboration in ProjectCollaboration.objects.select_related("project"):
        collaboration.created_at = collaboration.project.created_at
        collaboration.created_by = collaboration.project.created_by
        collaboration.updated_at = collaboration.project.updated_at
        collaboration.updated_by = collaboration.project.updated_by
        collaboration.save(
            update_fields=["created_at", "created_by", "updated_at", "updated_by"]
        )


def remove_created_at_and_by(apps, schema_editor):
    ProjectCollaboration = apps.get_model("jobserver", "ProjectCollaboration")
    ProjectCollaboration.objects.update(
        created_at=None, created_by=None, updated_at=None, updated_by=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0020_add_created_and_updated_at_and_by_to_projectcollaboration"),
    ]

    operations = [
        migrations.RunPython(
            copy_created_and_updated_fields_from_project_to_collaboration,
            remove_created_at_and_by,
        )
    ]
