from attrs import asdict
from django.conf import settings
from django.db import transaction
from interactive_templates import create_commit

from jobserver.github import _get_github_api

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
        token=settings.INTERACTIVE_GITHUB_TOKEN,
        force=force,
    )

    create_job_request(analysis_request, backend, sha, project_yaml)

    analysis_request.save()
    notify_analysis_request_submitted(analysis_request)

    return analysis_request


def create_job_request(analysis_request, backend, sha, project_yaml):
    workspace = analysis_request.project.interactive_workspace
    job_request = workspace.job_requests.create(
        backend=backend,
        created_by=analysis_request.created_by,
        sha=sha,
        project_definition=project_yaml,
        force_run_dependencies=True,
        requested_actions=["run_all"],
    )
    analysis_request.job_request = job_request


def resubmit_analysis(analysis_request, get_github_api=_get_github_api):
    repo = analysis_request.project.interactive_workspace.repo
    sha, project_yaml = get_existing_commit(analysis_request.id, repo, get_github_api)
    create_job_request(
        analysis_request, analysis_request.job_request.backend, sha, project_yaml
    )
    analysis_request.save()


def get_existing_commit(analysis_id, repo, get_github_api):
    if repo.url.startswith("http"):
        return _get_existing_commit_github(analysis_id, repo, get_github_api)
    else:  # support local repositories for testing
        return _get_existing_commit_local(analysis_id, repo)


def _get_existing_commit_github(analysis_id, repo, get_github_api):
    """Used for github repos, in production."""
    github_api = get_github_api()
    sha = github_api.get_tag_sha(repo.owner, repo.name, analysis_id)
    project_yaml = github_api.get_file(repo.owner, repo.name, analysis_id)
    return sha, project_yaml


def _get_existing_commit_local(analysis_id, repo):
    """Used for local repo, in testing."""
    from interactive_templates.create import git

    ps = git(
        "ls-remote",
        "--tags",
        repo.url,
        f"refs/tags/{analysis_id}",
        capture_output=True,
        check=True,
    )

    sha = ps.stdout[:40]

    ps = git("show", f"{sha}:project.yaml", capture_output=True, cwd=repo.url)
    project_yaml = ps.stdout.strip()

    return sha, project_yaml
