# Generated by Django 4.0.4 on 2022-06-08 15:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0013_copy_requested_actions_to_requested_actions2"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobrequest",
            name="requested_actions",
        ),
    ]
