from attrs import asdict
from django.conf import settings
from django.db import transaction
from interactive_templates import create_commit

from .models import AnalysisRequest
from .slacks import notify_analysis_request_submitted


@transaction.atomic()
def submit_analysis(
    *,
    analysis,
    backend,
    creator,
    project,
    purpose,
    report_title,
    title,
    force=False,
):
    """
    Create all the parts needed for an analysis

    This will stay in job-server while create_commit() is intended to move to
    an external service in the future.
    """

    # create an AnalysisRequest instance so we have a PK to use in various
    # places, but we don't save it until we've written the commit and pushed
    # it, so we can create the JobRequest this object needs
    analysis_request = AnalysisRequest(
        project=project,
        created_by=creator,
        updated_by=creator,
        title=title,
        purpose=purpose,
        report_title=report_title,
        template_data=asdict(analysis),
    )

    # update the Analysis structure so we can pass around a single object
    # if/when we pull the create_commit function out into another service
    # this structure would be the JSON we send over
    analysis.id = analysis_request.pk

    sha, project_yaml = create_commit(
        analysis,
        token=settings.GITHUB_WRITEABLE_TOKEN,
        force=force,
    )

    job_request = project.interactive_workspace.job_requests.create(
        backend=backend,
        created_by=creator,
        sha=sha,
        project_definition=project_yaml,
        force_run_dependencies=True,
        requested_actions=["run_all"],
    )

    analysis_request.job_request = job_request
    analysis_request.save()

    notify_analysis_request_submitted(analysis_request)

    return analysis_request
