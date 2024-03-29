# Generated by Django 5.0.1 on 2024-01-18 16:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0017_ensure_only_one_lead_org_for_a_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("created_at__isnull", False), ("created_by__isnull", False)
                ),
                name="jobserver_project_both_created_at_and_created_by_set",
            ),
        ),
    ]
