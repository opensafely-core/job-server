# Generated by Django 4.2.5 on 2023-09-06 16:15

from django.db import migrations

import jobserver.models.user


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0006_move_to_new_release_flow"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", jobserver.models.user.UserManager()),
            ],
        ),
    ]
