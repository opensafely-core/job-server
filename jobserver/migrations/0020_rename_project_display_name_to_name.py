# Generated by Django 3.1.2 on 2021-03-11 15:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0019_rename_project_name_to_slug"),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="display_name",
            new_name="name",
        ),
    ]
