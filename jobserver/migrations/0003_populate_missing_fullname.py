# Generated by Django 5.1.7 on 2025-03-21 16:25

import re

from django.db import migrations


system_accounts = {
    "opensafely-interactive": "OpenSAFELY Interactive",
    "reports-bot": "OpenSAFELY Reports Bot",
    "evilghickman": "George Hickman (test)",
}


def get_missing_fullname_from_email(user):
    nums_pattern = re.compile(r"\d+")

    email_local = nums_pattern.sub("", user.email.split("@")[0])
    alpha_email_parts = [part for part in email_local.split(".") if part]
    if len(alpha_email_parts) >= 2:
        return " ".join([part.title() for part in email_local.split(".")])


def get_missing_fullname_from_applications(user):
    for application in user.applications.all():
        if (
            hasattr(application, "contactdetailspage")
            and application.contactdetailspage.email == user.email
        ):
            return application.contactdetailspage.full_name


def populate_missing_fullname(apps, schema_editor):
    User = apps.get_model("jobserver", "User")
    nameless_users = User.objects.filter(fullname="")
    for user in nameless_users:
        user.fullname = (
            system_accounts.get(user.username, None)
            or get_missing_fullname_from_applications(user)
            or get_missing_fullname_from_email(user)
            or user.username
        )

    User.objects.bulk_update(nameless_users, ["fullname"])


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0002_remove_project_application_url"),
    ]

    operations = [
        migrations.RunPython(
            populate_missing_fullname,
            reverse_code=migrations.RunPython.noop,
        )
    ]
