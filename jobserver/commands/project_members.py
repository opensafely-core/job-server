from django.db import transaction
from django.utils import timezone

from ..authorization.utils import dotted_path
from ..models import AuditableEvent, ProjectMembership


@transaction.atomic()
def add(*, project, user, roles, by):
    membership = ProjectMembership(
        project=project,
        user=user,
        created_by=by,
        roles=roles,
    )
    membership.save(override=True)

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
def update_roles(*, membership, by, roles):
    AuditableEvent.objects.create(
        type=AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES,
        old=",".join([dotted_path(r) for r in membership.roles]),
        target_model=membership._meta.label,
        target_field="roles",
        target_id=membership.pk,
        target_user=membership.user.username,
        parent_model=membership.project._meta.label,
        parent_id=membership.project.pk,
        created_by=by.username,
        new=",".join([dotted_path(r) for r in roles]),
    )

    membership.roles = roles
    membership.save(update_fields=["roles"], override=True)


@transaction.atomic()
def remove(*, membership, by):
    # We remove the roles from the membership before we remove the membership to ensure
    # the audit log is complete: the membership may have been created before the audit
    # log existed, so may not contain an entry that records the roles associated with
    # the membership.
    update_roles(membership=membership, by=by, roles=[])

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

    membership.delete(override=True)
