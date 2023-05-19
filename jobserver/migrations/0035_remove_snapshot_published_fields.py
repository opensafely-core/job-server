# Generated by Django 4.1.9 on 2023-05-17 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "jobserver",
            "0034_rename_releasefilepublishrequest_to_snapshotpublishrequest",
        ),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="snapshot",
            name="jobserver_snapshot_both_published_at_and_published_by_set",
        ),
        migrations.RemoveField(
            model_name="snapshot",
            name="published_at",
        ),
        migrations.RemoveField(
            model_name="snapshot",
            name="published_by",
        ),
    ]