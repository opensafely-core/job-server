# Generated by Django 3.2.5 on 2021-08-02 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0058_add_snapshot_published_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="uses_new_release_flow",
            field=models.BooleanField(default=True),
        ),
    ]
