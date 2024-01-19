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
