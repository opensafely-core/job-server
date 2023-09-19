from django.db import models
from django.utils import timezone


class AuditableEvent(models.Model):
    """
    A table to track changes to our models

    We avoid ForeignKeys here so our audit log never interferes with our "live"
    data.
    """

    class Type(models.TextChoices):
        PROJECT_MEMBER_ADDED = "project_member_added", "User added"
        PROJECT_MEMBER_REMOVED = "project_member_removed", "User removed"
        PROJECT_MEMBER_UPDATED_ROLES = (
            "project_member_updated_roles",
            "User's roles updated",
        )

    old = models.TextField()
    new = models.TextField()

    # what is this record auditing?
    # we use this field to make it explicit what's being audited and to look up
    # related code, eg presenters
    type = models.TextField(choices=Type.choices)  # noqa: A003

    target_model = models.TextField()
    target_field = models.TextField()
    target_id = models.TextField()

    # most events happen to a user so make our lives easier and track their
    # username directly
    target_user = models.TextField()

    # some events are only relevant when their parent model/PK are known, for
    # example deleted memberships should still show up on the project audit log
    parent_model = models.TextField()
    parent_id = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.TextField()

    def __str__(self):
        return f"pk={self.pk} type={self.type}"
