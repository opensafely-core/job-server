# Generated by Django 3.1.2 on 2021-03-11 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0016_approve_existing_users"),
    ]

    operations = [
        migrations.AddField(
            model_name="org",
            name="slug",
            field=models.SlugField(default="", max_length=255, unique=True),
            preserve_default=False,
        ),
    ]
