from ...models import AuditableEvent
from .base import LinkableObject, PresentableAuditableEvent
from .project_members import _user, roles_str_to_class_name_str


def updated_roles(*, event: AuditableEvent) -> PresentableAuditableEvent:
    actor = LinkableObject.build(
        obj=_user(event.created_by),
        link_func="get_staff_url",
    )
    user = LinkableObject.build(
        obj=_user(event.target_user),
        link_func="get_staff_url",
    )
    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "created_at": event.created_at,
            "user": user,
            "before": roles_str_to_class_name_str(event.old),
            "after": roles_str_to_class_name_str(event.new),
        },
        template_name="staff/auditable_events/user_updated_roles.html",
    )
