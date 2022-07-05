import operator
from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import Least
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View
from first import first

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.github import get_repos_with_dates
from jobserver.models import Workspace


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoList(View):
    def get(self, request, *args, **kwargs):
        all_repos = list(get_repos_with_dates())

        # remove repos with the non-research topic
        all_repos = [r for r in all_repos if "non-research" not in r["topics"]]

        private_repos = [repo for repo in all_repos if repo["is_private"]]

        eleven_months_ago = timezone.now() - timedelta(days=30 * 11)

        # get workspaces with the first run job started_at annotated on
        workspaces = (
            Workspace.objects.exclude(project__slug="opensafely-testing")
            .annotate(num_jobs=Count("job_requests__jobs"))
            .filter(num_jobs__gt=0)
            .select_related("created_by", "project")
            .annotate(
                first_run=Least(
                    "job_requests__jobs__started_at", "job_requests__jobs__created_at"
                )
            )
            .filter(first_run__lt=eleven_months_ago)
        )

        # build up a list of dicts with repo URL and the first started_at date
        # as keys alongside the workspace.  This allows us to order by
        # first_run below.
        workspaces = [
            {
                "first_run": w.first_run,
                "repo": w.repo,
                "workspace": w,
            }
            for w in workspaces
        ]
        workspaces = sorted(workspaces, key=operator.itemgetter("first_run"))

        def merge_data(repo):
            """
            Merge our workspace and first run data with the data from GitHub

            Repos aren't unique to a workspace.  At the time of writing ~2/3 of
            repo URLs were duplicates, but we only care about the first time
            repo code was executed against patient data.

            Since the workspaces list has been ordered by the first started_at
            date of any Job in the Workspace we can use first() to find the
            first occurance of a repo URL based on Job.started_at.
            """
            workspace = first(workspaces, key=lambda w: w["repo"] == repo["url"])

            if workspace is not None:
                # extract the workspace object from our wrapper dictionary
                workspace = workspace["workspace"]

            # merge GitHub and our Workspace
            return repo | {"workspace": workspace}

        repos = list(merge_data(r) for r in private_repos)
        repos = list(
            r | {"has_releases": "github-releases" in r["topics"]} for r in repos
        )

        def exclude_never_run_repos(repos):
            """
            Exclude repos which we think can't have run a job

            Repos created after 2021-01-01 will almost certainly have used the
            job-server and thus if they have no workspace or jobs they haven't
            executed code on a backend.
            """
            for repo in repos:
                before_job_server = repo["created_at"] < datetime(
                    2021, 1, 1, tzinfo=timezone.utc
                )

                has_run_jobs = repo["workspace"] and repo["workspace"].first_run

                if before_job_server and not has_run_jobs:
                    continue

                yield repo

        repos = list(exclude_never_run_repos(repos))

        repos = sorted(repos, key=lambda r: r["created_at"])

        return TemplateResponse(request, "staff/repo_list.html", {"repos": repos})
