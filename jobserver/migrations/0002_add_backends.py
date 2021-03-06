# Generated by Django 3.1.2 on 2021-02-09 13:59

from django.db import migrations


def add_backends(apps, schema_editor):
    Backend = apps.get_model("jobserver", "Backend")

    Backend.objects.create(name="emis", display_name="EMIS")
    Backend.objects.create(name="expectations", display_name="expectations")
    Backend.objects.create(
        name="tpp",
        display_name="TPP",
        parent_directory="/d/Level4Files/workspaces",
    )


def remove_backends(apps, schema_editor):
    Backend = apps.get_model("jobserver", "Backend")

    Backend.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0001_initial"),
    ]

    operations = [migrations.RunPython(add_backends, reverse_code=remove_backends)]
