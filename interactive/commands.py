from django.db import transaction

from jobserver.authorization import InteractiveReporter
from jobserver.commands import project_members as members
from jobserver.models import OrgMembership, Report, User


@transaction.atomic()
def create_report(*, analysis_request, rfile, user):
    report = Report.objects.create(
        project=rfile.workspace.project,
        release_file=rfile,
        title=analysis_request.report_title,
        description="",
        created_by=user,
        updated_by=user,
    )
    analysis_request.report = report
    analysis_request.save(update_fields=["report"])

    return report


@transaction.atomic()
def create_user(*, creator, email, name, project):
    """Create an interactive user"""
    user = User.objects.create(
        fullname=name,
        email=email,
        username=email,
        created_by=creator,
    )

    OrgMembership.objects.bulk_create(
        OrgMembership(created_by=creator, org=org, user=user)
        for org in project.orgs.all()
    )

    members.add(
        project=project,
        user=user,
        roles=[InteractiveReporter],
        by=creator,
    )

    return user
