# Generated by Django 4.2.7 on 2023-11-06 14:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0009_remove_user_is_approved"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobrequest",
            name="codelists_ok",
            field=models.BooleanField(default=True),
        ),
    ]
