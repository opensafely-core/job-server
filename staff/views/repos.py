from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.github import get_repos_with_dates
from jobserver.models import Workspace


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoList(View):
    def get(self, request, *args, **kwargs):
        all_repos = list(get_repos_with_dates())

        private_repos = [repo for repo in all_repos if repo["is_private"]]

        repo_lut = {w.repo: w for w in Workspace.objects.select_related("project")}

        repos = [r | {"workspace": repo_lut.get(r["url"], None)} for r in private_repos]
        repos = sorted(repos, key=lambda r: r["created_at"])

        return TemplateResponse(request, "staff/repo_list.html", {"repos": repos})
