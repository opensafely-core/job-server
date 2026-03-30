from functools import partial

from django.db import transaction

from jobserver.slacks import notify_copilots_project_added

from ..models import AuditableEvent, Project, ProjectCollaboration


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


@transaction.atomic()
def edit(*, old, form, by):
    # TODO: switch to Form to decouple ModelForm usage here
    new = form.save(commit=False)
    new.updated_by = by
    new.save()

    form_orgs = form.cleaned_data["orgs"]
    new.orgs.set(
        form_orgs,
        through_defaults={"created_by": by, "updated_by": by},
    )
    # Set first org in form to lead. We expect at least one, and this seems
    # like a reasonable pick. For now, the forms happen to only allow exactly one
    # to be selected, but the model allows 0 or 1 leads, and this function
    # accepts multiple. Don't change it if there was already a lead org (defensively).
    org_links = ProjectCollaboration.objects.filter(project=new)
    lead_orgs = org_links.filter(is_lead=True)
    if not lead_orgs:
        org_links.filter(org=form_orgs[0]).update(is_lead=True)

    # check changed_data here instead of comparing self.object.project to
    # new.project because self.object is mutated when ModelForm._post_clean
    # updates the instance it was passed.  This is because form.instance is
    # set from the passed in self.object.
    if "slug" in form.changed_data:
        new.redirects.create(
            created_by=by,
            old_url=old.get_absolute_url(),
        )

    return new
