# Generated by Django 5.1.6 on 2025-03-13 18:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("interactive", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="analysisrequest",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="analysisrequest",
            name="job_request",
        ),
        migrations.RemoveField(
            model_name="analysisrequest",
            name="project",
        ),
        migrations.RemoveField(
            model_name="analysisrequest",
            name="report",
        ),
        migrations.RemoveField(
            model_name="analysisrequest",
            name="updated_by",
        ),
    ]
