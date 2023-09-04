# Generated by Django 4.2.4 on 2023-08-31 16:13

from django.db import migrations


def move_workspaces_to_new_release_flow(apps, schema_editor):
    Workspace = apps.get_model("jobserver", "Workspace")
    Workspace.objects.all().update(uses_new_release_flow=True)


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0005_add_job_run_command"),
    ]

    operations = [
        migrations.RunPython(
            move_workspaces_to_new_release_flow,
            reverse_code=migrations.RunPython.noop,
        )
    ]