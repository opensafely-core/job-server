from django.db import transaction
from django.utils import timezone

from ..authorization.utils import dotted_path
from ..models import AuditableEvent


@transaction.atomic()
def add(*, project, user, roles, by):
    membership = project.memberships.create(
        user=user,
        created_by=by,
        roles=roles,
        override=True,
    )

    # use a single timestamp in case we're also setting roles below and
    # want to match up records in the future
    now = timezone.now()

    # create this here because we can't pass a reference to the membership
    # before it's created
    AuditableEvent.objects.create(
        type=AuditableEvent.Type.PROJECT_MEMBER_ADDED,
        target_model=membership._meta.label,
        target_id=membership.pk,
        target_user=user.username,
        parent_model=project._meta.label,
        parent_id=project.pk,
        created_by=by.username,
        created_at=now,
    )

    if roles:
        # track the roles set as another event to save having to account
        # for all arbitrary data of any model on AuditableEvent
        AuditableEvent.objects.create(
            type=AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES,
            target_model=membership._meta.label,
            target_field="roles",
            target_id=membership.pk,
            target_user=user.username,
            parent_model=project._meta.label,
            parent_id=project.pk,
            new=",".join([dotted_path(r) for r in roles]),
            created_by=by.username,
            created_at=now,
        )

    return membership


@transaction.atomic()
def update_roles(*, member, by, roles):
    AuditableEvent.objects.create(
        type=AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES,
        old=",".join([dotted_path(r) for r in member.roles]),
        target_model=member._meta.label,
        target_field="roles",
        target_id=member.pk,
        target_user=member.user.username,
        parent_model=member.project._meta.label,
        parent_id=member.project.pk,
        created_by=by.username,
        new=",".join([dotted_path(r) for r in roles]),
    )

    member.roles = roles
    member.save(update_fields=["roles"])


@transaction.atomic()
def remove(*, membership, by):
    # We're removing the membership here so we need to save some details for
    # displaying that this happened as we won't be able to look them up at
    # render time.
    #
    # target_id uses the project PK so we can display this on the project's
    # logs page
    #
    # old uses the member's username so we can track who was removed
    AuditableEvent.objects.create(
        type=AuditableEvent.Type.PROJECT_MEMBER_REMOVED,
        target_model=membership._meta.label,
        target_id=membership.pk,
        target_user=membership.user.username,
        parent_model=membership.project._meta.label,
        parent_id=membership.project.pk,
        created_by=by.username,
    )

    membership.delete()
