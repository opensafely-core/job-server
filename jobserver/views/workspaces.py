import requests
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import CreateView, ListView, View
from first import first
from furl import furl
from opentelemetry import trace
from pybadges import badge

from ..authorization import has_permission
from ..forms import (
    WorkspaceArchiveToggleForm,
    WorkspaceCreateForm,
    WorkspaceNotificationsToggleForm,
)
from ..github import _get_github_api, get_repos_with_branches
from ..models import Backend, JobRequest, Project, Workspace
from ..releases import (
    build_hatch_token_and_url,
    build_outputs_zip,
    build_spa_base_url,
    workspace_files,
)


class WorkspaceArchiveToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
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

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        backend = get_object_or_404(Backend, slug=self.kwargs["backend_slug"])

        # ensure the user has access to the given Backend
        if request.user not in backend.members.all():
            raise Http404

        # we treat the ability to run jobs in this workspace and the ability to
        # interact with the backend (checked above) as permission to also view
        # the files those jobs have output
        if not has_permission(request.user, "job_run", project=workspace.project):
            raise Http404

        auth_token, url = build_hatch_token_and_url(
            backend=backend,
            workspace=workspace,
            user=request.user,
        )

        # add the path we're going to initialise the SPA with to the URL the
        # token was created for.
        f = furl(url)  # assume URL is a string
        f.path.segments += ["current"]

        base_path = build_spa_base_url(request.path, self.kwargs.get("path", ""))
        context = {
            "auth_token": auth_token,
            "backend": backend,
            "base_path": base_path,
            "files_url": f.url,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace_backend_files.html",
            context=context,
        )


class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project, org__slug=self.kwargs["org_slug"], slug=self.kwargs["project_slug"]
        )

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
                "workspace_create_error.html",
                context={"message": message, "project": self.project},
            )

        gh_org = first(self.request.user.orgs.first().github_orgs)
        if gh_org is None:
            message = (
                f"Your organisation, {self.project.org.name}, has no GitHub "
                "organisations associated with it, please contact support."
            )
            return TemplateResponse(
                request,
                "workspace_create_error.html",
                context={"message": message, "project": self.project},
            )

        try:
            self.repos_with_branches = list(get_repos_with_branches(gh_org))
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

    def form_valid(self, form):
        workspace = form.save(commit=False)
        workspace.created_by = self.request.user
        workspace.project = self.project
        workspace.save()

        return redirect(workspace)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            project=self.project,
            repos_with_branches=self.repos_with_branches,
            **kwargs,
        )

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "repos_with_branches": self.repos_with_branches,
        }


class WorkspaceDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        is_privileged_user = has_permission(
            request.user, "release_file_view", project=workspace.project
        )

        # a user can see backend files if they have access to at least one
        # backend and the permissions required to see outputs
        has_backends = (
            request.user.is_authenticated
            and request.user.backends.exclude(level_4_url="").exists()
        )
        can_view_files = is_privileged_user and has_backends

        # are there any releases to show for the workspace?
        can_view_releases = workspace.releases.exists()

        # unprivileged users can only see published snapshots, but privileged
        # users can see snapshots if there are any releases since they can also
        # prepare and publish them from the same views.
        has_published_snapshots = workspace.snapshots.exclude(
            published_at=None
        ).exists()
        has_any_snapshots = workspace.snapshots.exists()
        can_view_outputs = has_published_snapshots or (
            is_privileged_user and (can_view_releases or has_any_snapshots)
        )

        can_archive_workspace = has_permission(
            request.user, "workspace_archive", project=workspace.project
        )
        can_run_jobs = has_permission(
            request.user, "job_run", project=workspace.project
        )

        # should we display the releases section for this workspace?
        can_use_releases = can_view_files or can_view_releases or can_view_outputs

        try:
            repo_is_private = self.get_github_api().get_repo_is_private(
                workspace.repo_owner, workspace.repo_name
            )
        except requests.HTTPError:
            repo_is_private = None

        if has_permission(request.user, "job_request_pick_ref"):
            run_jobs_url = workspace.get_pick_ref_url()
        else:
            run_jobs_url = workspace.get_jobs_url()

        context = {
            "repo_is_private": repo_is_private,
            "run_jobs_url": run_jobs_url,
            "user_can_archive_workspace": can_archive_workspace,
            "user_can_run_jobs": can_run_jobs,
            "user_can_use_releases": can_use_releases,
            "user_can_view_files": can_view_files,
            "user_can_view_outputs": can_view_outputs,
            "user_can_view_releases": can_view_releases,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace_detail.html",
            context=context,
        )


class WorkspaceFileList(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        # we treat the ability to run jobs in this workspace and the ability to
        # interact with at least one backend (checked below) as permission to
        # also view the files those jobs have output on the backends
        if not has_permission(request.user, "job_run", project=workspace.project):
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
            "workspace_file_list.html",
            context=context,
        )


class WorkspaceLatestOutputsDetail(View):
    """
    Orchestrate viewing of the Workspace's outputs in the SPA

    We consume two URLs with one view, because we want to both do permissions
    checks on the Workspace but also load the SPA for any given path under the
    Workspace.
    """

    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
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
            "workspace_latest_outputs_detail.html",
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
            project__org__slug=self.kwargs["org_slug"],
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


class WorkspaceLog(ListView):
    paginate_by = 25
    template_name = "workspace_log.html"

    def dispatch(self, request, *args, **kwargs):
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("WorkspaceLog"):
            try:
                with tracer.start_as_current_span("get workspace"):
                    self.workspace = Workspace.objects.get(
                        project__org__slug=self.kwargs["org_slug"],
                        project__slug=self.kwargs["project_slug"],
                        name=self.kwargs["workspace_slug"],
                    )
            except Workspace.DoesNotExist:
                return redirect("/")

            with tracer.start_as_current_span("super().dispatch"):
                return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # limit backends to those the workspace uses
        backends = Backend.objects.filter(
            pk__in=JobRequest.objects.filter(workspace=self.workspace).values_list(
                "backend_id", flat=True
            )
        )

        return super().get_context_data(**kwargs) | {
            "backends": backends,
            "workspace": self.workspace,
        }

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(workspace=self.workspace)
            .select_related(
                "backend", "workspace", "workspace__project", "workspace__project__org"
            )
            .order_by("-pk")
        )

        q = self.request.GET.get("q")
        if q:
            qwargs = Q(jobs__action__icontains=q) | Q(jobs__identifier__icontains=q)
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(qwargs)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(qwargs | Q(jobs__pk=q))

        if backends := self.request.GET.getlist("backend"):
            qs = qs.filter(backend__slug__in=backends)

        return qs


class WorkspaceNotificationsToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
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
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        snapshots = workspace.snapshots.order_by("-created_at")

        can_view_all_files = has_permission(
            request.user, "release_file_view", project=workspace.project
        )
        if not can_view_all_files:
            snapshots = snapshots.exclude(published_at=None)

        context = {
            "user_can_view_all_files": can_view_all_files,
            "snapshots": snapshots,
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace_output_list.html",
            context=context,
        )


class WorkspaceOutputsBadge(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        published_snapshots = workspace.snapshots.exclude(published_at=None).count()

        s = badge(
            left_text="Published outputs",
            right_text=str(published_snapshots),
            right_color="#0058be",
        )
        return HttpResponse(s, headers={"Content-Type": "image/svg+xml"})
