from django.db import transaction

from ..models import Project, ProjectCollaboration


@transaction.atomic()
def add(*, by, name, number, orgs, application_url="", copilot=None):
    project = Project.objects.create(
        name=name,
        number=number,
        copilot=copilot,
        application_url=application_url,
        created_by=by,
        updated_by=by,
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

    return project


@transaction.atomic()
def edit(*, old, form, by):
    # TODO: switch to Form to decouple ModelForm usage here
    new = form.save(commit=False)
    new.updated_by = by
    new.save()

    new.orgs.set(
        form.cleaned_data["orgs"], through_defaults={"created_by": by, "updated_by": by}
    )

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
