from django.db import models
from django.utils import timezone


class ReleaseAuditEntry(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"

    actor = models.ForeignKey(
        "User",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )
    release = models.ForeignKey(
        "Release",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )

    event_type = models.TextField(choices=EventType.choices)

    created_at = models.DateTimeField(default=timezone.now)


class ReleaseFileAuditEntry(models.Model):
    class EventType(models.TextChoices):
        DELETED = "deleted", "Deleted"
        UPLOADED = "uploaded", "Uploaded"

    actor = models.ForeignKey(
        "User",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )
    release_file = models.ForeignKey(
        "ReleaseFile",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )

    event_type = models.TextField(choices=EventType.choices)

    created_at = models.DateTimeField(default=timezone.now)


class RoleAuditEntry(models.Model):
    class RoleEventType(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        UNASSIGNED = "unassigned", "Unassigned"

    assigner = models.ForeignKey(
        "User",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries_as_assigner",  # there might be a better name for these related_names!
    )
    assignee = models.ForeignKey(
        "User",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries_as_assignee",
    )
    group = models.ForeignKey(
        "Group",
        null=True,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries",
    )
    organisation = models.ForeignKey(
        "Organisation",
        null=True,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries",
    )
    project = models.ForeignKey(
        "Project",
        null=True,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries",
    )

    event = models.ForeignKey("AuditEvent", on_delete=models.PROTECT)

    created_at = models.DateTimeField(default=timezone.now)


class SnapshotAuditEntry(models.Model):
    class EventType(models.TextChoices):
        PREPARED = "prepared", "Prepared"
        PUBLISHED = "published", "Published"

    actor = models.ForeignKey(
        "User",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )
    snapshot = models.ForeignKey(
        "Snapshot",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="",
    )

    event_type = models.TextField(choices=EventType.choices)

    created_at = models.DateTimeField(default=timezone.now)
