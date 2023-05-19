# Generated by Django 4.1.7 on 2023-05-03 09:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0027_copy_approvals_to_decisions_fields"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="releasefilepublishrequest",
            name="jobserver_releasefilepublishrequest_both_approved_at_and_approved_by_set",
        ),
        migrations.RemoveConstraint(
            model_name="reportpublishrequest",
            name="jobserver_reportpublishrequest_both_approved_at_and_approved_by_set",
        ),
        migrations.RemoveField(
            model_name="releasefilepublishrequest",
            name="approved_at",
        ),
        migrations.RemoveField(
            model_name="releasefilepublishrequest",
            name="approved_by",
        ),
        migrations.RemoveField(
            model_name="reportpublishrequest",
            name="approved_at",
        ),
        migrations.RemoveField(
            model_name="reportpublishrequest",
            name="approved_by",
        ),
    ]