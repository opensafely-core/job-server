# Delete a project created in error and associated instances.
from django.db import migrations


def delete_project_dafadfads(apps, schema_editor):
    """Delete Project with name `dafadfads` and associated instances."""
    Project = apps.get_model("jobserver", "Project")
    AuditableEvent = apps.get_model("jobserver", "AuditableEvent")
    ProjectCollaboration = apps.get_model("jobserver", "ProjectCollaboration")

    try:
        project = Project.objects.get(name="dafadfads")
    except Project.DoesNotExist:
        print("0004: No project `dafadfads`, nothing to do")
        return
    # Save the project ID as we'll need it to look up the AuditableEvent after we've deleted the project.
    project_id = project.id

    deletions = []
    # We have to delete ProjectCollaboration before Project as they have a
    # protected relationship.
    deletions.append(
        ProjectCollaboration.objects.filter(project_id=project_id).delete()
    )
    # Also deletes ProjectMembership via CASCADE.
    deletions.append(project.delete())
    deletions.append(
        AuditableEvent.objects.filter(
            parent_model="jobserver.Project", parent_id=project_id
        ).delete()
    )

    # Provide some feedback.
    print(f"0004: Deleted {deletions}")


class Migration(migrations.Migration):
    dependencies = [
        ("maintenance", "0003_drop_django_admin_table"),
    ]

    operations = [
        migrations.RunPython(delete_project_dafadfads, migrations.RunPython.noop),
    ]
