"""Drop unused auth_user_* tables.

These tables would be used if we used the default Django User model, but we
extend it. They can be safely dropped.

These tables exist in production at the time of writing. auth_user has two rows
of very old data that is not relevant to the application as it exists today and
no relationship to the jobserver_user table. The other two tables are empty.

Keep django_auth_group and django_auth_permission et cetera as they could be
useful in replacing our roles implementation someday. And Django writes to
the permission tables for each model that is created, while django.contrib.auth
remains in INSTALLED_APPS.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("maintenance", "0001_delete_project_kasdlkfj"),
    ]

    # Need to drop the tables with FKs to auth_user first.
    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS auth_user_user_permissions;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS auth_user_groups;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS auth_user;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
