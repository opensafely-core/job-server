import itertools

import requests
import structlog
from csp.decorators import csp_exempt
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Min, Value
from django.db.models.functions import Least
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.github import _get_github_api
from jobserver.models import Project, ReleaseFile, Repo


logger = structlog.get_logger(__name__)


class MissingGitHubReposError(Exception):
    pass


def build_repos_by_project(projects, get_github_api=_get_github_api):
    """
    Build a dict with a list of repos indexed by project PK

    We need to get public/private status from GitHub and we want to do that in
    as few GraphQL and DB queries as possible.  This function gets all the
    relevant repos from the db, and from GitHub, and combines them up into a
    single structure.

    It returns a dict of project PK -> list of relevant repos, pulled from the
    list of combined ones.

    By building this structure up front we avoid various DB and HTTP queries.
    """
    # get all the Repo instances from the db
    db_repos = Repo.objects.filter(workspaces__project__in=projects).distinct()

    # Get a set of GitHub orgs so the API can pull repo details from each one
    repo_orgs = {r.owner for r in db_repos}

    try:
        github_repos = list(get_github_api().get_repos_with_status_and_url(repo_orgs))
    except requests.HTTPError:
        # if the GitHub API is down log some details but don't block the page
        logger.exception(
            "Failed to get repo status and URL from GitHub API", repo_orgs=repo_orgs
        )
        return {}

    # index GitHub repo dicts by URL so they're easier to lookup
    github_repos_by_url = {r["url"]: r for r in github_repos}

    # sense check that we're not missing any repos from GitHub.  We shouldn't
    # ever hit this path but it will be a lot easier to debug if we ever do
    # manage to get into this state.
    urls = {r.url for r in db_repos}
    if missing := urls - set(github_repos_by_url.keys()):
        output = "\n * ".join(missing)
        raise MissingGitHubReposError(f"Missing repo URLs: {output}")

    # merge the two representations of repo data into a single dict per repo
    repos = [
        {
            "get_staff_url": r.get_staff_url(),
            "is_private": github_repos_by_url[r.url]["is_private"],
            "name": r.name,
            "pk": r.pk,
        }
        for r in db_repos
    ]

    # Filter the repos for each project using the repos_ids we annotated onto
    # the QuerySet so we get {project_pk: repos} for each project on the page.
    return {p.pk: [r for r in repos if r["pk"] in p.repo_ids] for p in projects}


@method_decorator(require_role(CoreDeveloper), name="dispatch")
@method_decorator(csp_exempt, name="dispatch")
class Copiloting(TemplateView):
    get_github_api = staticmethod(_get_github_api)
    template_name = "staff/dashboards/copiloting.html"

    def get_context_data(self, **kwargs):
        # these orgs are not copiloted so we can ignore them here
        excluded_org_slugs = ["datalab", "lshtm", "university-of-bristol"]

        projects = (
            Project.objects.select_related("copilot", "org")
            .exclude(org__slug__in=excluded_org_slugs)
            .annotate(
                workspace_count=Count("workspaces", distinct=True),
                job_request_count=Count("workspaces__job_requests", distinct=True),
                date_first_run=Min(
                    Least(
                        "workspaces__job_requests__jobs__started_at",
                        "workspaces__job_requests__jobs__created_at",
                    )
                ),
                repo_ids=ArrayAgg(
                    "workspaces__repo_id", default=Value([]), distinct=True
                ),
            )
            .prefetch_related("workspaces__repo")
            .order_by("name")
        )

        release_files_by_project = itertools.groupby(
            ReleaseFile.objects.select_related("workspace__project")
            .exclude(workspace__project__org__slug__in=excluded_org_slugs)
            .order_by("workspace__project__pk")
            .iterator(),
            key=lambda f: f.workspace.project.pk,
        )
        file_counts_by_project = {
            p: len(list(files)) for p, files in release_files_by_project
        }

        repos_by_project = build_repos_by_project(
            projects=projects,
            get_github_api=self.get_github_api,
        )

        def iter_projects(projects, file_counts_by_project, repos_by_project):
            """
            Build a project representation

            Looking up a number of files released for a project as an annotation
            on the main `projects` query makes Postgres very unhappy and it's
            not obvious how to fix that from the query planner.  This function
            combines the ReleaseFile data (which we've grouped by Project PK) and
            the general project representation.

            Note: we could handle all stats this way but at the time of writing
            the current annotations were performant.
            """
            for project in projects:
                files_released_count = file_counts_by_project.get(project.pk, 0)
                repos = repos_by_project.get(project.pk, [])

                yield {
                    "copilot": project.copilot,
                    "date_first_run": project.date_first_run,
                    "files_released_count": files_released_count,
                    "get_staff_url": project.get_staff_url(),
                    "job_request_count": project.job_request_count,
                    "name": project.name,
                    "number": project.number,
                    "org": project.org,
                    "repos": repos,
                    "status": project.get_status_display(),
                    "workspace_count": project.workspace_count,
                }

        projects = list(
            sorted(
                iter_projects(
                    projects,
                    file_counts_by_project,
                    repos_by_project,
                ),
                key=lambda p: p["name"].lower(),
            )
        )

        return super().get_context_data(**kwargs) | {
            "projects": projects,
        }
