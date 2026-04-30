# Delete a project created in error and associated instances.
# See https://bennettoxford.slack.com/archives/C069SADHP1Q/p1777546132838079
from django.db import migrations


def delete_project_kasdlkfj(apps, schema_editor):
    """Delete Project with name `kasdlkfj` and associated instances."""
    Project = apps.get_model("jobserver", "Project")
    AuditableEvent = apps.get_model("jobserver", "AuditableEvent")
    ProjectCollaboration = apps.get_model("jobserver", "ProjectCollaboration")

    try:
        project = Project.objects.get(name="kasdlkfj")
    except Project.DoesNotExist:
        print("0001: No project `kasdlkfj`, nothing to do")
        return
    # Save this as will be updated to None after project delete.
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
    print(f"0001: Deleted {deletions}")


class Migration(migrations.Migration):
    dependencies = [
        ("jobserver", "0028_alter_project_name"),
    ]

    operations = [
        migrations.RunPython(delete_project_kasdlkfj, migrations.RunPython.noop),
    ]
