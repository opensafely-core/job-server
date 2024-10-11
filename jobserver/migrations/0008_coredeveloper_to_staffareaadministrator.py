# Generated by Django 5.1.1 on 2024-10-02 11:00

from django.db import migrations

from jobserver.authorization.roles import CoreDeveloper, StaffAreaAdministrator


def change_user_role(apps, from_role, to_role):
    User = apps.get_model("jobserver", "User")
    users = User.objects.filter(roles__contains=from_role)
    for user in users:
        user.roles.remove(from_role)
        user.roles.append(to_role)
    User.objects.bulk_update(users, ["roles"])


def coredeveloper_to_staffadministrator(apps, schema_editor):
    change_user_role(apps, CoreDeveloper, StaffAreaAdministrator)


def staffadministrator_to_coredeveloper(apps, schema_editor):
    change_user_role(apps, StaffAreaAdministrator, CoreDeveloper)


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0007_remove_user_is_staff_remove_user_is_superuser"),
    ]

    operations = [
        migrations.RunPython(
            coredeveloper_to_staffadministrator,
            reverse_code=staffadministrator_to_coredeveloper,
        )
    ]
