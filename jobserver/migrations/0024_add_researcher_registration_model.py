# Generated by Django 3.1.2 on 2021-03-12 12:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0023_add_form_a_fields_to_project"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResearcherRegistration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.TextField()),
                ("passed_researcher_training_at", models.DateTimeField()),
                ("is_ons_accredited_researcher", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="researcher_registrations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="project",
            name="researcher_registrations",
            field=models.ManyToManyField(
                related_name="projects", to="jobserver.ResearcherRegistration"
            ),
        ),
    ]
