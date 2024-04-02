from datetime import timedelta

import requests
from csp.decorators import csp_exempt
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Least
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import CreateView, FormView, ListView, View
from first import first
from furl import furl

from interactive.models import AnalysisRequest

from ..authorization import CoreDeveloper, has_permission, has_role, permissions
from ..forms import (
    WorkspaceArchiveToggleForm,
    WorkspaceCreateForm,
    WorkspaceEditForm,
    WorkspaceNotificationsToggleForm,
)
from ..github import _get_github_api
from ..models import (
    Backend,
    Job,
    JobRequest,
    Project,
    PublishRequest,
    Repo,
    Report,
    Workspace,
)
from ..releases import build_hatch_token_and_url, build_outputs_zip, workspace_files
from ..utils import build_spa_base_url


class WorkspaceAnalysisRequestList(ListView):
    context_object_name = "analysis_requests"
    model = AnalysisRequest
    template_name = "workspace/analysis_request_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(
            request.user,
            permissions.analysis_request_create,
            project=self.workspace.project,
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "workspace": self.workspace,
        }

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(job_request__workspace=self.workspace)
            .select_related("created_by", "project")
        )


class WorkspaceArchiveToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(
            request.user, "workspace_archive", project=workspace.project
        ):
            raise Http404

        form = WorkspaceArchiveToggleForm(request.POST)
        form.is_valid()

        workspace.is_archived = form.cleaned_data["is_archived"]
        workspace.save()

        return redirect(workspace.project)


class WorkspaceBackendFiles(View):
    """
    Orchestrate viewing of a Backend's "live" files for a given Workspace

    We consume two URLs with one view, because we want to both do permissions
    checks on the Workspace but also load the SPA for any given path under the
    Workspace.
    """

    @csp_exempt
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        backend = get_object_or_404(Backend, slug=self.kwargs["backend_slug"])

        # ensure the user has access to the given Backend
        if request.user not in backend.members.all():
            raise Http404

        if not has_permission(
            request.user,
            "unreleased_outputs_view",
            project=workspace.project,
        ):
            raise Http404

        auth_token, url = build_hatch_token_and_url(
            backend=backend,
            workspace=workspace,
            user=request.user,
        )

        # build the relevant URLs for the SPA by adding the necessary paths to
        # the URL the token was created for.
        files_url = (furl(url) / "current").url
        review_url = (furl(url) / "release").url

        base_path = build_spa_base_url(request.path, self.kwargs.get("path", ""))
        context = {
            "auth_token": auth_token,
            "backend": backend,
            "base_path": base_path,
            "files_url": files_url,
            "review_url": review_url,
            "workspace": workspace,
        }

        return TemplateResponse(
            request,
            "workspace/backend_files.html",
            context=context,
        )


class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    get_github_api = staticmethod(_get_github_api)
    model = Workspace
    template_name = "workspace/create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

        can_create_workspaces = has_permission(
            self.request.user,
            "workspace_create",
            project=self.project,
        )
        if not can_create_workspaces:
            raise Http404

        if not self.request.user.orgs.exists():
            message = (
                "Your user account has no organisation associated with it, "
                "please contact your Co-Pilot or support."
            )
            return TemplateResponse(
                request,
                "workspace/create_error.html",
                context={"message": message, "project": self.project},
            )

        org = self.request.user.orgs.first()
        gh_org = first(org.github_orgs)
        if gh_org is None:
            message = (
                f"Your organisation, {org.name}, has no GitHub organisations"
                "associated with it, please contact support."
            )
            return TemplateResponse(
                request,
                "workspace/create_error.html",
                context={"message": message, "project": self.project},
            )

        try:
            self.repos_with_branches = list(
                self.get_github_api().get_repos_with_branches(gh_org)
            )
        except requests.HTTPError:
            # gracefully handle not being able to access GitHub's API
            msg = (
                "An error occurred while retrieving the list of repositories from GitHub, "
                "please reload the page to try again."
            )
            messages.error(request, msg)
            return TemplateResponse(
                request,
                self.template_name,
                context={"project": self.project},
            )

        self.repos_with_branches = sorted(
            self.repos_with_branches, key=lambda r: r["name"].lower()
        )

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        repo, _ = Repo.objects.get_or_create(url=form.cleaned_data["repo"])

        workspace = Workspace.objects.create(
            name=form.cleaned_data["name"],
            purpose=form.cleaned_data["purpose"],
            branch=form.cleaned_data["branch"],
            created_by=self.request.user,
            updated_by=self.request.user,
            project=self.project,
            repo=repo,
        )

        return redirect(workspace)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            project=self.project,
            repos_with_branches=self.repos_with_branches,
            **kwargs,
        )

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)

        # WorkspaceCreateForm isn't a ModelForm so don't pass instance to it
        del kwargs["instance"]

        return kwargs | {
            "project": self.project,
            "repos_with_branches": self.repos_with_branches,
        }


class WorkspaceDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        # get the first job for this workspace's repo
        first_job = (
            Job.objects.filter(job_request__workspace__project=workspace.project)
            .annotate(run_at=Least("started_at", "created_at"))
            .order_by("run_at")
            .first()
        )

        # if the first job to run against this workspace's repo was more than
        # 11 months ago then show a warning
        eleven_months_ago = timezone.now() - timedelta(days=30 * 11)

        is_member = request.user in workspace.project.members.all()

        try:
            repo_is_private = self.get_github_api().get_repo_is_private(
                workspace.repo.owner, workspace.repo.name
            )
        except (requests.ConnectionError, requests.HTTPError):
            repo_is_private = None

        show_publish_repo_warning = (
            is_member
            and first_job
            and first_job.run_at < eleven_months_ago
            and repo_is_private
        )

        can_archive_workspace = has_permission(
            request.user, "workspace_archive", project=workspace.project
        )
        can_run_jobs = has_permission(
            request.user, permissions.job_run, project=workspace.project
        )
        can_toggle_notifications = has_permission(
            request.user, "workspace_toggle_notifications", project=workspace.project
        )
        has_backends = request.user.is_authenticated and request.user.backends.exists()

        # should we show the admin section in the UI?
        show_admin = (
            can_archive_workspace or repo_is_private or can_toggle_notifications
        )

        honeycomb_can_view_links = has_role(self.request.user, CoreDeveloper)

        is_interactive_user = has_permission(
            request.user, permissions.analysis_request_create, project=workspace.project
        )
        show_interactive_button = is_interactive_user and workspace.is_interactive

        outputs = self.get_output_permissions(request.user, workspace)

        if is_interactive_user:
            analyses = AnalysisRequest.objects.filter(
                job_request__workspace=workspace
            ).order_by("-created_at")[:5]
        else:
            analyses = []

        reports = Report.objects.filter(release_file__workspace=workspace)

        context = {
            "analyses": analyses,
            "first_job": first_job,
            "honeycomb_can_view_links": honeycomb_can_view_links,
            "honeycomb_link": f"https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/job-server?query=%7B%22time_range%22%3A2419200%2C%22granularity%22%3A0%2C%22breakdowns%22%3A%5B%22status%22%5D%2C%22calculations%22%3A%5B%7B%22op%22%3A%22HEATMAP%22%2C%22column%22%3A%22current_runtime%22%7D%5D%2C%22filters%22%3A%5B%7B%22column%22%3A%22name%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22update_job%22%7D%2C%7B%22column%22%3A%22workspace_name%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22{workspace.name}%22%7D%2C%7B%22column%22%3A%22completed%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3Atrue%7D%2C%7B%22column%22%3A%22status_change%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3Atrue%7D%5D%2C%22filter_combination%22%3A%22AND%22%2C%22orders%22%3A%5B%5D%2C%22havings%22%3A%5B%5D%2C%22limit%22%3A100%7D",
            "is_member": is_member,
            "outputs": outputs,
            "repo_is_private": repo_is_private,
            "reports": reports,
            "show_admin": show_admin,
            "show_interactive_button": show_interactive_button,
            "show_publish_repo_warning": show_publish_repo_warning,
            "user_can_archive_workspace": can_archive_workspace,
            "user_can_run_jobs": can_run_jobs,
            "user_can_toggle_notifications": can_toggle_notifications,
            "user_has_backends": has_backends,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace/detail.html",
            context=context,
        )

    def get_output_permissions(self, user, workspace):
        # a user can see backend files if they have access to at least one
        # backend and the permissions required to see outputs
        is_privileged_user = has_permission(
            user, "release_file_view", project=workspace.project
        )
        has_backends = (
            user.is_authenticated and user.backends.exclude(level_4_url="").exists()
        )
        can_view_files = is_privileged_user and has_backends

        # are there any releases to show for the workspace?
        can_view_releases = workspace.releases.exists()

        return {
            "level_4": {
                "disabled": not can_view_files,
            },
            "released": {
                "disabled": not can_view_releases,
            },
        }


class WorkspaceEdit(FormView):
    form_class = WorkspaceEditForm
    template_name = "workspace/edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        can_create_workspaces = has_permission(
            self.request.user,
            "workspace_create",
            project=self.workspace.project,
        )
        if not can_create_workspaces:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.workspace.purpose = form.cleaned_data["purpose"]
        self.workspace.save()
        return redirect(self.workspace)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "workspace": self.workspace,
        }

    def get_initial(self):
        return {"purpose": self.workspace.purpose}


class WorkspaceEventLog(ListView):
    paginate_by = 25
    template_name = "workspace/event_log.html"

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # limit backends to those the workspace uses
        backends = Backend.objects.filter(
            pk__in=JobRequest.objects.filter(workspace=self.workspace).values_list(
                "backend_id", flat=True
            )
        ).order_by("name")

        return super().get_context_data(**kwargs) | {
            "backends": backends,
            "workspace": self.workspace,
        }

    def get_queryset(self):
        qs = (
            JobRequest.objects.with_started_at()
            .filter(workspace=self.workspace)
            .select_related("backend", "workspace", "workspace__project")
            .order_by("-pk")
        )

        if q := self.request.GET.get("q"):
            qwargs = Q(jobs__action__icontains=q) | Q(jobs__identifier__icontains=q)
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(qwargs)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number or job request ID
                qs = qs.filter(qwargs | Q(jobs__pk=q) | Q(id=q))

        if backends := self.request.GET.getlist("backend"):
            qs = qs.filter(backend__slug__in=backends)

        return qs


class WorkspaceFileList(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(
            request.user,
            "unreleased_outputs_view",
            project=workspace.project,
        ):
            raise Http404

        backends = request.user.backends.exclude(level_4_url="").order_by("slug")

        if not backends:
            raise Http404

        context = {
            "backends": backends,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace/file_list.html",
            context=context,
        )


class WorkspaceLatestOutputsDetail(View):
    """
    Orchestrate viewing of the Workspace's outputs in the SPA

    We consume two URLs with one view, because we want to both do permissions
    checks on the Workspace but also load the SPA for any given path under the
    Workspace.
    """

    @csp_exempt
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        # only a privileged user can view the current files
        if not has_permission(
            request.user, "release_file_view", project=workspace.project
        ):
            raise Http404

        # only show the publish button if the user has permission to publish
        # ouputs
        can_publish = has_permission(
            request.user, "snapshot_create", project=workspace.project
        )
        prepare_url = workspace.get_create_snapshot_api_url() if can_publish else ""

        base_path = build_spa_base_url(request.path, self.kwargs.get("path", ""))
        context = {
            "base_path": base_path,
            "files_url": workspace.get_releases_api_url(),
            "prepare_url": prepare_url,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace/latest_outputs_detail.html",
            context=context,
        )


class WorkspaceLatestOutputsDownload(View):
    """
    Orchestrate viewing of the Workspace's outputs in the SPA

    We consume two URLs with one view, because we want to both do permissions
    checks on the Workspace but also load the SPA for any given path under the
    Workspace.
    """

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not workspace.files.exists():
            raise Http404

        # only a privileged user can view the current files
        if not has_permission(
            request.user, "release_file_view", project=workspace.project
        ):
            raise Http404

        # get the latest files as an iterable of ReleaseFile instances
        latest_files = workspace_files(workspace).values()

        zf = build_outputs_zip(latest_files, request.build_absolute_uri)
        return FileResponse(
            zf,
            as_attachment=True,
            filename=f"workspace-{workspace.name}.zip",
        )


class WorkspaceNotificationsToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(
            request.user, "workspace_toggle_notifications", project=workspace.project
        ):
            raise Http404

        form = WorkspaceNotificationsToggleForm(data=request.POST)
        form.is_valid()

        workspace.should_notify = form.cleaned_data["should_notify"]
        workspace.save()

        return redirect(workspace)


class WorkspaceOutputList(ListView):
    """
    Show a list of Outputs versions for a Workspace

    Outputs in this context are a combination of "the latest version of each
    ReleaseFile for the Workspace" and any Snapshots for the Workspace.
    """

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        snapshots = workspace.snapshots.order_by("-created_at")

        can_view_all_files = has_permission(
            request.user, "release_file_view", project=workspace.project
        )
        if not can_view_all_files:
            snapshots = snapshots.filter(
                publish_requests__decision=PublishRequest.Decisions.APPROVED
            )

        context = {
            "user_can_view_all_files": can_view_all_files,
            "snapshots": snapshots,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace/output_list.html",
            context=context,
        )
