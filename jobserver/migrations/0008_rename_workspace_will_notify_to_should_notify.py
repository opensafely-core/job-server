# Generated by Django 3.1.2 on 2021-01-28 13:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0007_add_jobrequest_will_notify"),
    ]

    operations = [
        migrations.RenameField(
            model_name="workspace",
            old_name="will_notify",
            new_name="should_notify",
        ),
    ]
