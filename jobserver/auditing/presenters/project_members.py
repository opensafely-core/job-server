from .base import LinkableObject, PresentableAuditableEvent
from .utils import lookup_project, lookup_user, roles_str_to_class_name_str


def added(*, event):
    actor_user_obj = lookup_user(event.created_by)
    actor = LinkableObject.build(
        obj=actor_user_obj,
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user_obj = lookup_user(event.target_user)
    user = LinkableObject.build(
        obj=user_obj,
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "actor_user_obj": actor_user_obj,
            "created_at": event.created_at,
            "project": project,
            "user": user,
            "user_obj": user_obj,
        },
        template_name="staff/auditable_events/project/members/added.html",
    )


def updated_roles(*, event):
    actor_user_obj = lookup_user(event.created_by)

    actor = LinkableObject.build(
        obj=actor_user_obj,
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user_obj = lookup_user(event.target_user)
    user = LinkableObject.build(
        obj=user_obj,
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "actor_user_obj": actor_user_obj,
            "created_at": event.created_at,
            "project": project,
            "user": user,
            "user_obj": user_obj,
            "before": roles_str_to_class_name_str(event.old),
            "after": roles_str_to_class_name_str(event.new),
        },
        template_name="staff/auditable_events/project/members/updated_roles.html",
    )


def removed(*, event):
    actor_user_obj = lookup_user(event.created_by)

    actor = LinkableObject.build(
        obj=actor_user_obj,
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user_obj = lookup_user(event.target_user)
    user = LinkableObject.build(
        obj=user_obj,
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "actor_user_obj": actor_user_obj,
            "created_at": event.created_at,
            "project": project,
            "user": user,
            "user_obj": user_obj,
        },
        template_name="staff/auditable_events/project/members/removed.html",
    )
