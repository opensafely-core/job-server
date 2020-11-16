# Generated by Django 3.1.2 on 2020-11-16 14:32

import re

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0022_add_workspace_name_slug_validator"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workspace",
            name="name",
            field=models.TextField(
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    )
                ],
            ),
        ),
    ]
