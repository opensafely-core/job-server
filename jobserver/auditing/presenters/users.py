from ...models import AuditableEvent
from .base import LinkableObject, PresentableAuditableEvent
from .utils import lookup_user, roles_str_to_class_name_str


def updated_roles(*, event: AuditableEvent) -> PresentableAuditableEvent:
    actor_user_obj = lookup_user(event.created_by)

    actor = LinkableObject.build(
        obj=actor_user_obj,
        link_func="get_staff_url",
    )
    user = LinkableObject.build(
        obj=lookup_user(event.target_user),
        link_func="get_staff_url",
    )
    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "actor_user_obj": actor_user_obj,
            "created_at": event.created_at,
            "user": user,
            "before": roles_str_to_class_name_str(event.old),
            "after": roles_str_to_class_name_str(event.new),
        },
        template_name="staff/auditable_events/user_updated_roles.html",
    )
