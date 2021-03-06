# Generated by Django 3.1.2 on 2021-02-16 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0008_rename_workspace_will_notify_to_should_notify"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="email",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="project_lead",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="proposed_duration",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="project",
            name="proposed_start_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
