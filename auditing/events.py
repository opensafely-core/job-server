import attr
from django.db import connection

from jobserver.models import Release, ReleaseFile, Snapshot, User
from jobserver.models.core import UserAuditEvent
from jobserver.models.outputs import (
    ReleaseAuditEvent,
    ReleaseFileAuditEvent,
    SnapshotAuditEvent,
)

from .models import AuditEvent, RoleAuditEvent


def get_obj_or_id(model, pk, field=None):
    try:
        obj = model.objects.get(pk=pk)
    except model.DoesNotExist:
        name = obj._meta.model.__name__
        return f"{name} ID={pk} (deleted)"

    if field is None:
        return obj

    return getattr(obj, field)


def get_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H-%M-%s%z")


@attr.frozen
class ReleaseCreated:
    event_id = attr.ib()
    creator_id = attr.ib()
    release_id = attr.ib()

    @classmethod
    def create(cls, creator_id, release_id, role_name):
        event_data = {
            "creator": creator_id,
            "release": release_id,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.RELEASE_CREATED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ user to the event as the creator
            UserAuditEvent.objects.create(
                event=event,
                user_id=creator_id,
                relationship_type=UserAuditEvent.UserEventType.RELEASE_CREATED,
            )

            # Link an Actual™ release to the event
            ReleaseAuditEvent.objects.create(
                event=event,
                release_id=release_id,
                relationship_type=ReleaseAuditEvent.ReleaseEventType.CREATED,
            )

        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.RELEASE_CREATED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        creator = get_obj_or_id(User, self.creator_id, field="username")
        release = get_obj_or_id(Release, self.release_id)

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{creator} {event_type} {release} at {timestamp}"


@attr.frozen
class ReleaseFileDeleted:
    event_id = attr.ib()
    deleter_id = attr.ib()
    release_file_id = attr.ib()

    @classmethod
    def create(cls, deleter_id, release_file_id):
        event_data = {
            "deleter": deleter_id,
            "release_file": release_file_id,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.RELEASE_FILE_UPLOADED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ release file to the event
            ReleaseFileAuditEvent.objects.create(
                event=event,
                release_file_id=release_file_id,
                relationship_type=ReleaseFileAuditEvent.ReleaseFileEventType.UPLOADED,
            )

            # Link an Actual™ user to the event as the deleter
            UserAuditEvent.objects.create(
                event=event,
                user_id=deleter_id,
                relationship_type=UserAuditEvent.UserEventType.RELEASE_FILE_DELETED,
            )

        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.RELEASE_FILE_DELETED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        deleter = get_obj_or_id(User, self.deleter_id, field="username")
        release_file = get_obj_or_id(ReleaseFile, self.release_file_id)

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{deleter} {event_type} {release_file} at {timestamp}"


@attr.frozen
class ReleaseFileUploaded:
    event_id = attr.ib()
    uploader_id = attr.ib()
    release_file_id = attr.ib()

    @classmethod
    def create(cls, uploader_id, release_file_id):
        event_data = {
            "uploader": uploader_id,
            "release_file": release_file_id,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.RELEASE_FILE_UPLOADED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ release file to the event
            ReleaseFileAuditEvent.objects.create(
                event=event,
                release_file_id=release_file_id,
                relationship_type=ReleaseFileAuditEvent.ReleaseFileEventType.UPLOADED,
            )

            # Link an Actual™ user to the event as the uploader
            UserAuditEvent.objects.create(
                event=event,
                user_id=uploader_id,
                relationship_type=UserAuditEvent.UserEventType.RELEASE_FILE_UPLOADER,
            )

        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.RELEASE_FILE_UPLOADED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        uploader = get_obj_or_id(User, self.uploader_id, field="username")
        release_file = get_obj_or_id(ReleaseFile, self.release_file_id)

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{uploader} {event_type} {release_file} at {timestamp}"


@attr.frozen
class RoleAssignment:
    event_id = attr.ib()
    assigner_id = attr.ib()
    assigned_id = attr.ib()
    role = attr.ib()

    @classmethod
    def create(cls, assigner_id, assigned_id, role_name):
        event_data = {
            "assigner": assigner_id,
            "assigned": assigned_id,
            "role": role_name,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.ROLE_ASSIGNED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ role to the event
            RoleAuditEvent.objects.create(
                event=event,
                role=role_name,
                relationship_type=RoleAuditEvent.RoleEventType.ASSIGNED,
            )

            # Link an Actual™ user to the event as the assigner
            UserAuditEvent.objects.create(
                event=event,
                user_id=assigner_id,
                relationship_type=UserAuditEvent.UserEventType.ROLE_ASSIGNER,
            )

            # Link an Actual™ user to the event as the assignee
            UserAuditEvent.objects.create(
                event=event,
                user_id=assigned_id,
                relationship_type=UserAuditEvent.UserEventType.ROLE_ASSIGNED,
            )
        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.ROLE_ASSIGNED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        assigner = get_obj_or_id(User, self.assigner, field="username")
        assignee = get_obj_or_id(User, self.assignee, field="username")

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{assigner} {event_type} {self.role} to {assignee} at {timestamp}"


@attr.frozen
class RoleUnAssignment:
    event_id = attr.ib()
    unassigner_id = attr.ib()
    unassigned_id = attr.ib()
    role = attr.ib()

    @classmethod
    def create(cls, unassigner_id, unassigned_id, role_name):
        event_data = {
            "unassigner": unassigner_id,
            "unassigned": unassigned_id,
            "role": role_name,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.ROLE_UNASSIGNED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ role to the event
            RoleAuditEvent.objects.create(
                event=event,
                role=role_name,
                relationship_type=RoleAuditEvent.RoleEventType.UNASSIGNED,
            )

            # Link an Actual™ user to the event as the assigner
            UserAuditEvent.objects.create(
                event=event,
                user_id=unassigner_id,
                relationship_type=UserAuditEvent.UserEventType.ROLE_UNASSIGNER,
            )

            # Link an Actual™ user to the event as the assignee
            UserAuditEvent.objects.create(
                event=event,
                user_id=unassigned_id,
                relationship_type=UserAuditEvent.UserEventType.ROLE_UNASSIGNED,
            )
        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.ROLE_UNASSIGNED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        assigner = get_obj_or_id(User, self.assigner, field="username")
        assignee = get_obj_or_id(User, self.assignee, field="username")

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{assigner} {event_type} {self.role} to {assignee} at {timestamp}"


@attr.frozen
class SnapshotPrepared:
    event_id = attr.ib()
    preparer_id = attr.ib()
    snapshot_id = attr.ib()

    @classmethod
    def create(cls, preparer_id, snapshot_id):
        event_data = {
            "preparer": preparer_id,
            "snapshot": snapshot_id,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.ASSIGN_ROLE,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ role to the event
            SnapshotAuditEvent.objects.create(
                event=event,
                snapshot_id=snapshot_id,
                relationship_type=SnapshotAuditEvent.SnapshotEventType.PREPARED,
            )

            # Link an Actual™ user to the event as the assignee
            UserAuditEvent.objects.create(
                event=event,
                user_id=preparer_id,
                relationship_type=UserAuditEvent.UserEventType.SNAPSHOT_PREPARED,
            )
        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.SNAPSHOT_PREPARED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        preparer = get_obj_or_id(User, self.preparer_id, field="username")
        snapshot = get_obj_or_id(Snapshot, self.snapshot_id)

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{preparer} {event_type} {snapshot} at {timestamp}"


@attr.frozen
class SnapshotPublished:
    event_id = attr.ib()
    publisher_id = attr.ib()
    snapshot_id = attr.ib()

    @classmethod
    def create(cls, publisher_id, snapshot_id):
        event_data = {
            "publisher": publisher_id,
            "snapshot": snapshot_id,
        }
        with connection.atomic():
            # store all the base event data
            event = AuditEvent.objects.create(
                event_type=AuditEvent.EventType.SNAPSHOT_PUBLISHED,
                event_type_version=1,
                event_data=event_data,
            )

            # Link an Actual™ role to the event
            SnapshotAuditEvent.objects.create(
                event=event,
                snapshot_id=snapshot_id,
                relationship_type=SnapshotAuditEvent.SnapshotEventType.PUBLISHED,
            )

            # Link an Actual™ user to the event as the assignee
            UserAuditEvent.objects.create(
                event=event,
                user_id=publisher_id,
                relationship_type=UserAuditEvent.UserEventType.SNAPSHOT_PUBLISHED,
            )
        return cls(event_id=event.id, **event_data)

    @classmethod
    def from_db(cls, db_obj):
        assert db_obj.event_type == AuditEvent.EventType.SNAPSHOT_PUBLISHED
        assert db_obj.event_type_version == 1
        return cls(event_id=db_obj.id, **db_obj.event_data)

    def __str__(self):
        event = AuditEvent.objects.get(pk=self.event_id)

        publisher = get_obj_or_id(User, self.publisher_id, field="username")
        snapshot = get_obj_or_id(Snapshot, self.snapshot_id)

        event_type = event.event_type.value
        timestamp = get_timestamp(event.created_at)

        return f"{publisher} {event_type} {snapshot} at {timestamp}"
