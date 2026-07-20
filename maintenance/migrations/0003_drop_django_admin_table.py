"""Drop unused auth_user_* tables.

This table would be used if django.contrib.admin were in INSTALLED_APPS, but
it is not. We use the staff pages instead.  It can be safely dropped.

This tables exist in production at the time of writing. It has 29 rows of data
recording admin actions taken in 2021 until commit
19981b23fa3c759721d2f6ea00ee2a86072aecf7 that disabled the admin site and
removed it from installed apps. They relate to very early setting up of
organisations and users in Job Server.This is not relevant to the application
as it exists today and long predates our audit log system which was added in
2024.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("maintenance", "0002_drop_django_auth_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS django_admin_log;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
