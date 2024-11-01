import itertools
from urllib.parse import quote, unquote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from furl import furl

from ..emails import (
    send_repo_signed_off_notification_to_researchers,
    send_repo_signed_off_notification_to_staff,
)
from ..github import GitHubError, _get_github_api
from ..models import Org, Project, ProjectMembership, Repo
from ..slacks import notify_copilots_of_repo_sign_off


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
        "get_edit_url": workspace.get_edit_url(),
        "is_archived": workspace.is_archived,
        "name": workspace.name,
        "get_readme_url": workspace.get_readme_url(),
        "project": workspace.project,
        "purpose": workspace.purpose,
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
                    "name": f.path.segments[-1],
                    "url": repo_url,
                },
            }
            return TemplateResponse(request, "project/repo_list.html", context=context)

        projects = Project.objects.filter(workspaces__repo=repo).distinct()

        if projects.count() == 1:
            return redirect(projects.first())

        context = {
            "projects": projects,
            "repo": repo,
        }

        return TemplateResponse(request, "project/repo_list.html", context=context)


@method_decorator(login_required, name="dispatch")
class SignOffRepo(TemplateView):
    get_github_api = staticmethod(_get_github_api)

    def dispatch(self, request, *args, **kwargs):
        self.repo = get_object_or_404(Repo, url=unquote(self.kwargs["repo_url"]))

        self.workspaces = self.repo.workspaces.select_related(
            "created_by", "project"
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

            # notify the workspace creators this has happened so they get a
            # chance to contact us if there is an error
            send_repo_signed_off_notification_to_researchers(self.repo)

            if not self.repo.has_github_outputs:
                # notify the copilots that a repo has been signed off by a user
                notify_copilots_of_repo_sign_off(self.repo)
            else:
                send_repo_signed_off_notification_to_staff(self.repo)

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
        except GitHubError:
            is_private = None

        repo = {
            "has_github_outputs": self.repo.has_github_outputs,
            "is_private": is_private,
            "name": self.repo.name,
            "researcher_signed_off_at": self.repo.researcher_signed_off_at,
            "researcher_signed_off_by": self.repo.researcher_signed_off_by,
            "status": "private" if is_private else "public",
            "url": self.repo.url,
        }

        try:
            workspaces = [build_workspace(w, github_api) for w in self.workspaces]
        except GitHubError:
            workspaces = []

        # build up a list of branches without a workspace

        try:
            branches = [
                b["name"]
                for b in github_api.get_branches(self.repo.owner, self.repo.name)
            ]
            workspace_branches = [w["branch"] for w in workspaces]
            branches = [b for b in branches if b not in workspace_branches]
        except GitHubError:
            branches = []

        workspaces_signed_off = not self.workspaces.filter(signed_off_at=None).exists()

        # TODO: when we have dealt with all the cross-project repos and are
        # enforcing repos can't be used across projects this check can be
        # skipped.
        projects = Project.objects.filter(workspaces__repo=self.repo).distinct()
        if projects.count() == 1:
            project = projects.first()
            project_status = project.get_status_display()

            # quote this so the already quoted sign-off URL isn't unquoted when
            # Django renders it, and the level of quotation on the sign-off URL
            # is preserved for use in the ?next query arg
            sign_off_url = quote(self.repo.get_sign_off_url(), safe="")

            project_url = project.get_edit_url() + f"?next={sign_off_url}"
        else:
            project_status = None
            project_url = self.repo.get_handler_url()

        context = super().get_context_data() | {
            "workspaces_signed_off": workspaces_signed_off,
            "branches": branches,
            "repo": repo,
            "project_status": project_status,
            "project_url": project_url,
            "workspaces": workspaces,
        }

        return TemplateResponse(
            request=self.request,
            template="repo/sign_off.html",
            context=context,
        )
