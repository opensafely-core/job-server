from datetime import timedelta
from urllib.parse import quote

import structlog
from csp.decorators import csp_exempt
from django.db.models import Count, Min, Prefetch
from django.db.models.functions import Least, Lower
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View
from first import first

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.github import _get_github_api
from jobserver.models import Project, Repo, Workspace


logger = structlog.get_logger(__name__)


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class PrivateReposDashboard(View):
    get_github_api = staticmethod(_get_github_api)

    @csp_exempt
    def get(self, request, *args, **kwargs):
        """
        List private repos which are in need of converting to public

        Repos should be:
         * Private
         * not have `non-research` topic
         * first job was run > 11 months ago
        """
        all_repos = list(self.get_github_api().get_repos_with_dates("opensafely"))

        # remove repos with the non-research topic
        all_repos = [r for r in all_repos if "non-research" not in r["topics"]]

        private_repos = [repo for repo in all_repos if repo["is_private"]]

        all_workspaces = list(
            Workspace.objects.exclude(project__slug="opensafely-testing")
            .select_related("created_by", "project", "repo")
            .annotate(num_jobs=Count("job_requests__jobs"))
            .annotate(
                first_run=Min(
                    Least(
                        "job_requests__jobs__started_at",
                        "job_requests__jobs__created_at",
                    )
                ),
            )
        )

        all_projects = list(Project.objects.all())

        def enhance(repo):
            """
            Enhance the repo dict from get_repos_with_dates() with workspace data

            We need to filter repos, not workspaces, so this gives us all the
            information we need when filtering further down.
            """
            # get workspaces just for this repo
            workspaces = [
                w for w in all_workspaces if repo["url"].lower() == w.repo.url.lower()
            ]
            workspaces = sorted(workspaces, key=lambda w: w.name.lower())

            project_ids = [w.project_id for w in workspaces]
            projects = [p for p in all_projects if p.pk in project_ids]

            # get workspaces which have run jobs
            with_jobs = [w for w in workspaces if w.first_run]

            # sorting by a datetime puts the workspaces into oldest job first
            with_jobs = sorted(with_jobs, key=lambda w: w.first_run)

            # get the first workspace to have run a job
            workspace = first(with_jobs, key=lambda w: w.first_run)

            # get first_run as either None or a datetime
            first_run = workspace.first_run if workspace else None

            # has this repo ever had jobs run with it?
            has_jobs = sum(w.num_jobs for w in workspaces) > 0

            # how many of the workspaces have been signed-off for being published?
            signed_off = sum(1 for w in workspaces if w.signed_off_at)

            return repo | {
                "first_run": first_run,
                "has_jobs": has_jobs,
                "has_github_outputs": "github-releases" in repo["topics"],
                "projects": projects,
                "quoted_url": quote(repo["url"], safe=""),
                "signed_off": signed_off,
                "workspace": workspace,
                "workspaces": workspaces,
            }

        # add workspace (and related object) data to repos
        repos = [enhance(r) for r in private_repos]

        eleven_months_ago = timezone.now() - timedelta(days=30 * 11)

        def select(repo):
            """
            Select a repo based on various predicates below.

            We're already working with private repos here so we check

            * Has jobs or a workspace
            * First job to run happened over 11 months ago
            """
            if not (repo["workspaces"] and repo["has_jobs"]):
                logger.info("No workspaces/jobs", url=repo["url"])
                return False

            # because we know we have at least one job and first_run looks at
            # either started_at OR created_at we know we will always have a
            # value for first_run at this point
            first_ran_over_11_months_ago = repo["first_run"] < eleven_months_ago
            if not first_ran_over_11_months_ago:
                logger.info("First run <11mo ago", url=repo["url"])
                return False

            return True

        # select only repos we care about
        repos = [r for r in repos if select(r)]

        return TemplateResponse(
            request, "staff/dashboards/repos.html", {"repos": repos}
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ReposWithMultipleProjects(View):
    @csp_exempt
    def get(self, request, *args, **kwargs):
        def iter_repos():
            repos = (
                Repo.objects.annotate(
                    project_count=Count("workspaces__project", distinct=True)
                )
                .filter(project_count__gte=2)
                .prefetch_related(
                    Prefetch(
                        "workspaces",
                        Workspace.objects.order_by("name"),
                        to_attr="ordered_workspaces",
                    ),
                    # Prefetch(
                    #     "workspaces__project", Project.objects.all(), to_attr="derp"
                    # ),
                )
                .order_by(Lower("url"))
            )

            for repo in repos:
                projects = Project.objects.filter(workspaces__repo=repo).distinct()
                yield {
                    "has_github_outputs": repo.has_github_outputs,
                    "name": repo.name,
                    "projects": projects,
                    "quoted_url": repo.quoted_url,
                    "workspaces": repo.ordered_workspaces,
                }

        repos = list(iter_repos())
        return TemplateResponse(
            request,
            "staff/dashboards/repos_with_multiple_projects.html",
            {"repos": repos},
        )
