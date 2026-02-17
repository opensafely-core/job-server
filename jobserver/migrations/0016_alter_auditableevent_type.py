from django.db import migrations, models
from django.db.models import F


PROJECT_CREATED = "project_created"
UNKNOWN_USER = "Unknown User"


def add_project_created_events(apps, _schema_editor):
    """
    Ensure every project has one "project_created" audit event.

    This migration is safe to re-run:
    - existing events are updated if parent fields are blank
    - new events are only created for projects that do not have one yet
    """
    AuditableEvent = apps.get_model("jobserver", "AuditableEvent")
    Project = apps.get_model("jobserver", "Project")
    project_model = Project._meta.label

    project_created_events = AuditableEvent.objects.filter(
        type=PROJECT_CREATED,
        target_model=project_model,
    )

    # Backfill missing parent fields for older rows
    project_created_events.filter(parent_model="").update(parent_model=project_model)
    project_created_events.filter(parent_id="").update(parent_id=F("target_id"))

    projects_with_events = set(
        project_created_events.exclude(target_id="").values_list("target_id", flat=True)
    )

    events_to_create = []
    for project in Project.objects.select_related("created_by"):
        project_id = str(project.pk)
        if project_id in projects_with_events:
            continue

        created_by = (
            project.created_by.username if project.created_by_id else UNKNOWN_USER
        )
        events_to_create.append(
            AuditableEvent(
                type=PROJECT_CREATED,
                old="",
                new="",
                target_model=project_model,
                target_field="",
                target_id=project_id,
                target_user=created_by,
                parent_model=project_model,
                parent_id=project_id,
                created_at=project.created_at,
                created_by=created_by,
            )
        )

    if events_to_create:
        AuditableEvent.objects.bulk_create(events_to_create, batch_size=1000)


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0015_alter_auditableevent_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditableevent",
            name="type",
            field=models.TextField(
                choices=[
                    ("project_created", "Project created"),
                    ("project_member_added", "User added"),
                    ("project_member_removed", "User removed"),
                    ("project_member_updated_roles", "User's roles updated"),
                    ("user_updated_roles", "User's global roles updated"),
                ]
            ),
        ),
        migrations.RunPython(
            add_project_created_events,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
