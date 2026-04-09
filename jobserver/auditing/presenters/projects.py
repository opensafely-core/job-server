"""Presenters for project creation audit log entries."""

from jobserver.models import AuditableEvent

from .base import LinkableObject, PresentableAuditableEvent
from .utils import lookup_project, lookup_user


def created(*, event: AuditableEvent) -> PresentableAuditableEvent:
    """Build a presentable event for project creation."""

    actor_user_obj = lookup_user(event.created_by)

    actor = LinkableObject.build(
        obj=actor_user_obj,
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
            "actor_user_obj": actor_user_obj,
        },
        template_name="staff/auditable_events/project/created.html",
    )
