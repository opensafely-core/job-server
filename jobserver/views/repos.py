import itertools
from urllib.parse import unquote

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from furl import furl

from ..github import _get_github_api
from ..models import Org, Project, ProjectMembership, Repo


def build_workspace(workspace, github_api):
    branch_exists = bool(
        github_api.get_branch(
            workspace.repo.owner,
            workspace.repo.name,
            workspace.branch,
        )
    )

    return {
        "signed_off_at": workspace.signed_off_at,
        "signed_off_by": workspace.signed_off_by,
        "branch": workspace.branch,
        "branch_exists": branch_exists,
        "get_absolute_url": workspace.get_absolute_url(),
        "is_archived": workspace.is_archived,
        "name": workspace.name,
        "get_readme_url": workspace.get_readme_url(),
        "project": workspace.project,
    }


class RepoHandler(View):
    def get(self, request, *args, **kwargs):
        repo_url = unquote(self.kwargs["repo_url"])

        known_orgs = set(
            itertools.chain.from_iterable(
                Org.objects.values_list("github_orgs", flat=True)
            )
        )
        allowed_orgs = tuple(f"https://github.com/{org}" for org in known_orgs)

        if not repo_url.startswith(allowed_orgs):
            raise Http404

        try:
            repo = Repo.objects.get(url=repo_url)
        except Repo.DoesNotExist:
            f = furl(repo_url)

            # ensure we have owner and name parts of the URL, even if they're meaningless
            if len(f.path.segments) < 2:
                raise Http404

            context = {
                "projects": [],
                "repo": {
                    "owner": f.path.segments[-2],
                    "name": f.path.segments[-1],
                    "url": repo_url,
                },
            }
            return TemplateResponse(request, "project_repo_list.html", context=context)

        projects = Project.objects.filter(workspaces__repo=repo).distinct()

        if projects.count() == 1:
            return redirect(projects.first())

        context = {
            "projects": projects,
            "repo": repo,
        }

        return TemplateResponse(request, "project_repo_list.html", context=context)


@method_decorator(login_required, name="dispatch")
class SignOffRepo(TemplateView):
    get_github_api = staticmethod(_get_github_api)

    def dispatch(self, request, *args, **kwargs):
        self.repo = get_object_or_404(Repo, url=unquote(self.kwargs["repo_url"]))

        if not self.repo.has_sign_offs_enabled:
            raise Http404

        self.workspaces = self.repo.workspaces.select_related(
            "created_by", "project", "project__org"
        ).order_by("name")

        # is the user a member of any of the workspace's Projects?
        is_member = ProjectMembership.objects.filter(
            project__workspaces__in=self.workspaces, user=request.user
        ).exists()

        if not (is_member and self.workspaces.exists()):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", None)

        # all workspaces have been signed off
        all_signed_off = not self.workspaces.filter(signed_off_at=None).exists()

        if not (name or all_signed_off):
            messages.error(
                request, "Please sign off all workspaces before signing off the repo"
            )
            return self.render_to_response()

        if name is None:
            self.repo.researcher_signed_off_at = timezone.now()
            self.repo.researcher_signed_off_by = request.user
            self.repo.save()
            return redirect("/")

        # we have a name in the form which means we're looking at an action for
        # the workspace with that name
        workspace = self.workspaces.filter(name=name).first()

        # a workspace can only be signed off once
        if workspace.signed_off_at:
            # TODO: should we even tell the user this? They shouldn't be able
            # to hit this outcome, and they can't do anything about it either
            return self.render_to_response()

        workspace.signed_off_at = timezone.now()
        workspace.signed_off_by = request.user
        workspace.save()

        return redirect(self.repo.get_sign_off_url())

    def render_to_response(self):
        github_api = self.get_github_api()

        try:
            is_private = github_api.get_repo_is_private(self.repo.owner, self.repo.name)
        except requests.HTTPError:
            is_private = None

        repo = {
            "is_private": is_private,
            "name": f"{self.repo.owner}/{self.repo.name}",
            "researcher_signed_off_at": self.repo.researcher_signed_off_at,
            "researcher_signed_off_by": self.repo.researcher_signed_off_by,
            "status": "private" if is_private else "public",
            "url": self.repo.url,
        }

        workspaces = [build_workspace(w, github_api) for w in self.workspaces]

        # build up a list of branches without a workspace
        branches = [
            b["name"] for b in github_api.get_branches(self.repo.owner, self.repo.name)
        ]
        workspace_branches = [w["branch"] for w in workspaces]
        branches = [b for b in branches if b not in workspace_branches]

        workspaces_signed_off = not self.workspaces.filter(signed_off_at=None).exists()

        context = super().get_context_data() | {
            "workspaces_signed_off": workspaces_signed_off,
            "branches": branches,
            "repo": repo,
            "workspaces": workspaces,
        }

        return TemplateResponse(
            request=self.request,
            template="sign_off_repo.html",
            context=context,
        )
