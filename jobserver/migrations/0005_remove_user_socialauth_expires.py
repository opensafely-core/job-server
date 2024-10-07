# Generated by Django 5.1.1 on 2024-09-13 11:20

from django.db import migrations
from social_django.models import UserSocialAuth


def remove_user_socialauth_expires(apps, schema_editor):
    users = UserSocialAuth.objects.filter(extra_data__has_key="expires")
    for user in users:
        del user.extra_data["expires"]
    UserSocialAuth.objects.bulk_update(users, ["extra_data"])


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0004_remove_orgmembership_roles"),
        ("social_django", "0016_alter_usersocialauth_extra_data"),
    ]

    operations = [
        migrations.RunPython(
            remove_user_socialauth_expires, reverse_code=migrations.RunPython.noop
        )
    ]