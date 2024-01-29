from ...models import Project, User
from .base import LinkableObject, PresentableAuditableEvent


def _project(*, pk, default="a Project"):
    try:
        return Project.objects.get(pk=pk)
    except (Project.DoesNotExist, ValueError):
        # handle a ValueError here because Django will (helpfully!) try to cast
        # the given pk to an int for BigAutoFields.  However
        # AuditableEvent's target_id and parent_id are TextFields which default
        # to an empty string, we can't guarantee that's been populated, and
        # int("") raises a ValueError.
        return default


def _user(s):
    try:
        return User.objects.get(username=s)
    except User.DoesNotExist:
        return s if s else "Unknown User"


def added(*, event):
    actor = LinkableObject.build(
        obj=_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=_project(pk=event.parent_id),
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
            "project": project,
            "user": user,
        },
        template_name="staff/auditable_events/project/members/added.html",
    )


def updated_roles(*, event):
    def _roles(roles_string):
        """
        Turn saved roles into display names

        We store roles as the repr's of their values, eg

            <class 'jobserver.authorization.roles.ProjectDeveloper'>

        This allows us to keep the creation of field changes generic.  However
        we need to turn these into something meaningful for display.
        """
        roles = roles_string.split(",")
        names = [r.rsplit(".")[-1] for r in roles]
        return ", ".join(names)

    actor = LinkableObject.build(
        obj=_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=_project(pk=event.parent_id),
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
            "project": project,
            "user": user,
            "before": _roles(event.old),
            "after": _roles(event.new),
        },
        template_name="staff/auditable_events/project/members/updated_roles.html",
    )


def removed(*, event):
    actor = LinkableObject.build(
        obj=_user(event.created_by),
        link_func="get_staff_url",
    )
    project = LinkableObject.build(
        obj=_project(pk=event.parent_id),
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
            "project": project,
            "user": user,
        },
        template_name="staff/auditable_events/project/members/removed.html",
    )
