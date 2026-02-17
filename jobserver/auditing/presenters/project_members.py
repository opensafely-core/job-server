from .base import LinkableObject, PresentableAuditableEvent
from .utils import lookup_project, lookup_user, roles_str_to_class_name_str


def added(*, event):
    actor = LinkableObject.build(
        obj=lookup_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user = LinkableObject.build(
        obj=lookup_user(event.target_user),
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "created_at": event.created_at,
            "project": project,
            "user": user,
        },
        template_name="staff/auditable_events/project/members/added.html",
    )


def updated_roles(*, event):
    actor = LinkableObject.build(
        obj=lookup_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user = LinkableObject.build(
        obj=lookup_user(event.target_user),
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "created_at": event.created_at,
            "project": project,
            "user": user,
            "before": roles_str_to_class_name_str(event.old),
            "after": roles_str_to_class_name_str(event.new),
        },
        template_name="staff/auditable_events/project/members/updated_roles.html",
    )


def removed(*, event):
    actor = LinkableObject.build(
        obj=lookup_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=lookup_project(pk=event.parent_id),
        link_func="get_staff_url",
    )
    user = LinkableObject.build(
        obj=lookup_user(event.target_user),
        link_func="get_staff_url",
    )

    return PresentableAuditableEvent(
        context={
            "actor": actor,
            "created_at": event.created_at,
            "project": project,
            "user": user,
        },
        template_name="staff/auditable_events/project/members/removed.html",
    )
