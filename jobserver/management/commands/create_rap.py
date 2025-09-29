"""Management command to create Jobs for a Job Request via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver.github import _get_github_api
from jobserver.models import Backend, User, Workspace
from jobserver.pipeline_config import get_codelists_status, get_project


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to create Jobs for a Job Request via the RAP API."""

    help = "Create RAP jobs via the RAP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "workspace",
            type=str,
            help="Workspace name.",
        )
        parser.add_argument(
            "user",
            type=str,
            help="Username of the user creating this RAP",
        )
        parser.add_argument(
            "backend",
            type=str,
            help="Backend this RAP will run on",
        )
        parser.add_argument(
            "-a",
            "--actions",
            nargs="+",
            type=str,
            help="Actions to run.",
        )
        parser.add_argument(
            "--commit",
            type=str,
            help="Git commit; defaults to workspace branch head",
        )
        parser.add_argument("--force-run-dependencies", action="store_true")

    def handle(self, *args, **options):
        workspace = Workspace.objects.get(name=options["workspace"])
        github_api = _get_github_api()

        if (commit := options.get("commit")) is None:
            # if a commit wasn't passed in, convert the branch to a sha
            commit = github_api.get_branch_sha(
                workspace.repo.owner,
                workspace.repo.name,
                workspace.branch,
            )

        codelists_status = get_codelists_status(
            workspace.repo.owner,
            workspace.repo.name,
            commit,
        )
        codelists_ok = codelists_status == "ok"

        backend = Backend.objects.get(slug=options["backend"])

        project = get_project(
            workspace.repo.owner,
            workspace.repo.name,
            commit,
        )

        job_request = backend.job_requests.create(
            workspace=workspace,
            created_by=User.objects.get(username=options["user"]),
            sha=commit,
            project_definition=project,
            codelists_ok=codelists_ok,
            requested_actions=options["actions"],
            cancelled_actions=[],
            force_run_dependencies=options["force_run_dependencies"],
        )

        job_request.request_rap_creation()
