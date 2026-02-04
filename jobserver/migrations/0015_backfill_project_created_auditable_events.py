from django.db import migrations


def add_project_created_events(apps, schema_editor):
    AuditableEvent = apps.get_model("jobserver", "AuditableEvent")
    Project = apps.get_model("jobserver", "Project")

    existing = set(
        AuditableEvent.objects.filter(
            type="project_created",
            target_model=Project._meta.label,
        ).values_list("target_id", flat=True)
    )

    events = []
    for project in Project.objects.select_related("created_by").all():
        target_id = str(project.pk)
        if target_id in existing:
            continue
        created_by = (
            project.created_by.username if project.created_by_id else "Unknown User"
        )
        events.append(
            AuditableEvent(
                type="project_created",
                target_model=Project._meta.label,
                target_id=target_id,
                target_user=created_by,
                created_at=project.created_at,
                created_by=created_by,
            )
        )

    if events:
        AuditableEvent.objects.bulk_create(events, batch_size=1000)


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0014_alter_user_backends_alter_user_orgs_and_more"),
    ]

    operations = [
        migrations.RunPython(add_project_created_events, migrations.RunPython.noop)
    ]
