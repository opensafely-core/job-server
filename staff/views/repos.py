import operator

from django.db.models.functions import Least
from django.template.response import TemplateResponse
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

        # get workspaces with the first run job started_at annotated on
        workspaces = (
            Workspace.objects.exclude(project__slug="opensafely-testing")
            .select_related("created_by", "project")
            .annotate(
                first_run=Least(
                    "job_requests__jobs__started_at", "job_requests__jobs__created_at"
                )
            )
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
        repos = sorted(repos, key=lambda r: r["created_at"])

        return TemplateResponse(request, "staff/repo_list.html", {"repos": repos})
