from functools import partial

from django.db import transaction

from jobserver.slacks import notify_copilots_project_added

from ..models import AuditableEvent, Project, ProjectCollaboration, User


@transaction.atomic()
def add(*, by, name, number, orgs, copilot=None):
    project = Project.objects.create(
        name=name,
        number=number,
        copilot=copilot,
        created_by=by,
        updated_by=by,
    )

    AuditableEvent.objects.create(
        type=AuditableEvent.Type.PROJECT_CREATED,
        target_model=Project._meta.label,
        target_id=project.pk,
        target_user=by.username,
        parent_model=Project._meta.label,
        parent_id=project.pk,
        created_by=by.username,
        created_at=project.created_at,
    )

    lead, *other = orgs
    ProjectCollaboration.objects.create(
        project=project,
        org=lead,
        is_lead=True,
        created_by=by,
        updated_by=by,
    )
    for org in other:
        ProjectCollaboration.objects.create(
            project=project,
            org=org,
            is_lead=False,
            created_by=by,
            updated_by=by,
        )

    # Send a Slack notificaton if and only if the entire transaction (including
    # any outer transaction) commits successfully - if the database actually updates.
    transaction.on_commit(partial(notify_copilots_project_added, project))

    return project


ALLOWED_EDIT_FIELDS = {
    "copilot",
    "copilot_notes",
    "copilot_support_ends_at",
    "name",
    "number",
    "orgs",
    "slug",
    "status",
    "status_description",
}
"""Set of Project field names accepted for update by actions.projects.edit."""


@transaction.atomic()
def edit(*, project: Project, fields: dict, by: User):
    """Update some Project fields.

    Handles configuring Org relationships and setting up redirects."""
    # Take a copy so we don't mutate the parameter as a side-effect.
    fields = dict(fields)

    # Check only valid values passed in.
    unknown_fields = fields.keys() - ALLOWED_EDIT_FIELDS
    if unknown_fields:
        raise ValueError(f"Unknown fields: {unknown_fields}")

    # Create required ProjectCollaboration for Org relationships, and set the
    # lead Org if required.
    if "orgs" in fields:
        fields_orgs = fields.pop("orgs")
        project.orgs.set(
            fields_orgs,
            through_defaults={"created_by": by, "updated_by": by},
        )
        # Set first org in form to lead. We expect at least one, and this seems
        # like a reasonable pick. For now, the forms happen to only allow exactly one
        # to be selected, but the model allows 0 or 1 leads, and this function
        # accepts multiple. Don't change it if there was already a lead org (defensively).
        org_links = ProjectCollaboration.objects.filter(project=project)
        lead_orgs = org_links.filter(is_lead=True)
        if fields_orgs and not lead_orgs:
            org_links.filter(org=fields_orgs[0]).update(is_lead=True)

    # Set up a redirect if the slug changed.
    if "slug" in fields and fields["slug"] != project.slug:
        project.redirects.create(
            created_by=by,
            old_url=project.get_absolute_url(),
        )

    # Do the updates and return.
    fields["updated_by"] = by
    for field, value in fields.items():
        setattr(project, field, value)
    project.save()
    return project
