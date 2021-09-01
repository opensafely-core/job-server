from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    """
    Core audit trail model

    This stores types of event which can happen.  For example a role being
    applied by a User to a User/Membership would have an "assign role" event.
    """

    class EventType(models.TextChoices):
        RELEASE_CREATED = "release_created", "Release Created"
        RELEASE_FILE_DELETED = "release_file_deleted", "Release File Deleted"
        RELEASE_FILE_UPLOADED = "release_file_uploaded", "Release File Uploaded"
        ROLE_ASSIGNED = "role_assigned", "Role Assigned"
        ROLE_UNASSIGNED = "role_unassigned", "Role Unssigned"
        SNAPSHOT_PREPARED = "snapshot_prepared", "Snapshot Prepared"
        SNAPSHOT_PUBLISHED = "snapshot_published", "Snapshot Published"

    event_type = models.TextField(choices=EventType.choices)
    event_data = models.JSONField()

    # Track version in case of schema changes
    event_type_version = models.IntegerField()

    created_at = models.DateTimeField(default=timezone.now)


class RoleAuditEvent(models.Model):
    class RoleTypes(models.TextChoices):
        PROJECTDEVELOPER = "project_developer", "ProjectDeveloper"

    class RoleEventType(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        UNASSIGNED = "unassigned", "Unassigned"

    event = models.ForeignKey("AuditEvent", on_delete=models.PROTECT)

    role = models.TextField(choices=RoleTypes.choices)
    relationship_type = models.TextField(choices=RoleEventType.choices)
