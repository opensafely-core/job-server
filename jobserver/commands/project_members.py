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
