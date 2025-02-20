from django.db import transaction

from jobserver.models import Report


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
