"""Presenters for project creation audit log entries."""

from jobserver.models import Project, User

from .base import LinkableObject, PresentableAuditableEvent


def lookup_project(*, pk, default="a Project"):
    try:
        return Project.objects.get(pk=pk)
    except (Project.DoesNotExist, ValueError):
        # handle a ValueError here because Django will (helpfully!) try to cast
        # the given pk to an int for BigAutoFields.  However
        # AuditableEvent's target_id and parent_id are TextFields which default
        # to an empty string, we can't guarantee that's been populated, and
        # int("") raises a ValueError.
        return default


def lookup_user(s):
    try:
        return User.objects.get(username=s)
    except User.DoesNotExist:
        return s if s else "Unknown User"


def created(*, event):
    """Build a presentable event for project creation."""
    actor = LinkableObject.build(
        obj=lookup_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "created_at": event.created_at,
            "project": project,
        },
        template_name="staff/auditable_events/project/created.html",
    )
