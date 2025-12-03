# Record 'start of audit log' events for all existing user's global roles
# (including []). Otherwise we cannot reconstruct the state before the first
# change for each user.
#
# Otherwise it is not possible to answer "list all the users that had role x on
# date y" or "list the date range this user had role x for" type questions that
# we may need to answer, not directly from the audit logs at least - so we
# would also have to combine with the current state if that user never had
# their roles changed since, which is messier.
#
# If you log the deltas you also want a logged definition of the state at time
# 0, when you introduce the logs, so that you can just analyse logs between 0
# and y. (We can't be precise for dates before date 0 when the audit logs are
# introduced). Some users would never appear in the logs after time 0, if they
# never change global roles since then.


from django.db import migrations

from jobserver.authorization.utils import dotted_path


#     type=AuditableEvent.type.USER_UPDATED_ROLES,
#         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# AttributeError: 'DeferredAttribute' object has no attribute 'USER_UPDATED_ROLES'
hardcoded_type = "user_updated_roles"


def create_baseline_audit_logs(apps, schema_editor):
    """Create audit log entries for all existing user roles as a baseline."""
    AuditableEvent = apps.get_model("jobserver", "AuditableEvent")
    User = apps.get_model("jobserver", "User")

    users = User.objects.all()

    audit_logs = []

    for user in users:
        audit_logs.append(
            AuditableEvent(
                type=hardcoded_type,
                old=",".join([dotted_path(r) for r in user.roles]),
                target_model=user._meta.label,
                target_field="roles",
                target_id=user.pk,
                target_user=user.username,
                new=",".join([dotted_path(r) for r in user.roles]),
            )
        )
    AuditableEvent.objects.bulk_create(audit_logs, batch_size=1000)

    print(
        f"Created {len(audit_logs)} baseline audit log entries for {len(users)} users"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0014_alter_user_backends_alter_user_orgs_and_more"),
    ]

    operations = [
        migrations.RunPython(create_baseline_audit_logs, migrations.RunPython.noop),
    ]
