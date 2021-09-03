from django.db import models
from django.utils import timezone


def get_object_or_deleted(obj, field=None):
    if obj is None:
        # TODO: can we get the object ID here?
        return "<deleted>"

    if field is not None:
        return getattr(obj, field)

    return str(obj)


def get_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H-%M-%s%z")


class ReleaseCreatedAuditEntry(models.Model):
    creator = models.ForeignKey(
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        creator = get_object_or_deleted(self.creator, field="username")
        timestamp = get_timestamp(self.created_at)

        return f"{creator} created Release ID={self.release_id} at {timestamp}"


class ReleaseFileDeletedAuditEntry(models.Model):
    deleter = models.ForeignKey(
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        deleter = get_object_or_deleted(self.deleter, field="username")
        timestamp = get_timestamp(self.created_at)

        return f"{deleter} deleted ReleaseFile ID={self.release_file_id} at {timestamp}"


class ReleaseFileUploadedAuditEntry(models.Model):
    uploader = models.ForeignKey(
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        uploader = get_object_or_deleted(self.uploader, field="username")
        timestamp = get_timestamp(self.created_at)

        return (
            f"{uploader} uploaded ReleaseFile ID={self.release_file_id} at {timestamp}"
        )


class RoleChangeAuditEntry(models.Model):
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
    project = models.ForeignKey(
        "Project",
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
    group = models.ForeignKey(
        "Group",
        null=True,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="role_change_audit_entries",
    )

    was_assigned = models.BooleanField()  # False if role was removed
    role = models.CharField()

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        assigner = get_object_or_deleted(self.assigner, field="username")
        assignee = get_object_or_deleted(self.assignee, field="username")

        event_type = "assigned" if self.was_assigned else "unassigned"
        timestamp = get_timestamp(self.created_at)

        return f"{assigner} {event_type} {self.role} to {assignee} at {timestamp}"


class SnapshotPreparedAuditEntry(models.Model):
    creator = models.ForeignKey(
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        creator = get_object_or_deleted(self.creator, field="username")
        timestamp = get_timestamp(self.created_at)

        return f"{creator} prepared Snapshot ID={self.snapshot_id} at {timestamp}"


class SnapshotPublishedAuditEntry(models.Model):
    creator = models.ForeignKey(
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

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        creator = get_object_or_deleted(self.creator, field="username")
        timestamp = get_timestamp(self.created_at)

        return f"{creator} published Snapshot ID={self.snapshot_id} at {timestamp}"
