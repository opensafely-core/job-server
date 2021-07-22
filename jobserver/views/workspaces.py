from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, View

from ..authorization import CoreDeveloper, has_permission, has_role
from ..backends import backends_to_choices
from ..forms import (
    JobRequestCreateForm,
    WorkspaceArchiveToggleForm,
    WorkspaceCreateForm,
    WorkspaceNotificationsToggleForm,
)
from ..github import get_branch_sha, get_repo_is_private, get_repos_with_branches
from ..models import Backend, JobRequest, Project, Workspace
from ..project import get_actions, get_project, load_yaml
from ..roles import can_run_jobs


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class WorkspaceArchiveToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        form = WorkspaceArchiveToggleForm(request.POST)
        form.is_valid()

        workspace.is_archived = form.cleaned_data["is_archived"]
        workspace.save()

        return redirect("/")


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project, org__slug=self.kwargs["org_slug"], slug=self.kwargs["project_slug"]
        )

        gh_org = self.request.user.orgs.first().github_orgs[0]
        self.repos_with_branches = sorted(
            get_repos_with_branches(gh_org), key=lambda r: r["name"].lower()
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
        kwargs = super().get_form_kwargs()
        kwargs["repos_with_branches"] = self.repos_with_branches
        return kwargs


class WorkspaceDetail(CreateView):
    form_class = JobRequestCreateForm
    model = JobRequest
    template_name = "workspace_detail.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                name=self.kwargs["workspace_slug"],
            )
        except Workspace.DoesNotExist:
            return redirect("/")

        if not request.user.is_authenticated:
            return TemplateResponse(
                request,
                self.template_name,
                context={"workspace": self.workspace},
            )

        self.user_can_run_jobs = can_run_jobs(request.user)

        self.show_details = self.user_can_run_jobs and not self.workspace.is_archived

        if not self.show_details:
            # short-circuit for logged out users to avoid the hop to grab
            # actions from GitHub
            self.actions = []
            return super().dispatch(request, *args, **kwargs)

        action_status_lut = self.workspace.get_action_status_lut()

        # build actions as list or render the exception to the page
        gh_org = self.request.user.orgs.first().github_orgs[0]
        try:
            self.project = get_project(
                gh_org,
                self.workspace.repo_name,
                self.workspace.branch,
            )
            data = load_yaml(self.project)
        except Exception as e:
            self.actions = []
            # this is a bit nasty, need to mirror what get/post would set up for us
            self.object = None
            context = self.get_context_data(actions_error=str(e))
            return self.render_to_response(context=context)

        self.actions = list(get_actions(data, action_status_lut))
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        gh_org = self.request.user.orgs.first().github_orgs[0]
        sha = get_branch_sha(gh_org, self.workspace.repo_name, self.workspace.branch)

        backend = Backend.objects.get(name=form.cleaned_data.pop("backend"))
        backend.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            project_definition=self.project,
            **form.cleaned_data,
        )
        return redirect(
            "workspace-logs",
            org_slug=self.workspace.project.org.slug,
            project_slug=self.workspace.project.slug,
            workspace_slug=self.workspace.name,
        )

    def get_context_data(self, **kwargs):
        can_use_releases = has_role(self.request.user, CoreDeveloper)

        # unprivileged users only see the Outputs button if there's published snapshots
        # privileged users see it if there's snapshots or workspace files
        is_privileged_user = has_permission(
            self.request.user, "view_release_file", project=self.workspace.project
        )
        if is_privileged_user:
            can_view_outputs = self.workspace.files.exists()
        else:
            can_view_outputs = self.workspace.snapshots.exclude(
                published_at=None
            ).exists()

        return super().get_context_data(**kwargs) | {
            "actions": self.actions,
            "can_use_releases": can_use_releases,
            "repo_is_private": self.get_repo_is_private(),
            "latest_job_request": self.get_latest_job_request(),
            "show_details": self.show_details,
            "user_can_run_jobs": self.user_can_run_jobs,
            "user_can_view_outputs": can_view_outputs,
            "workspace": self.workspace,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actions"] = [a["name"] for a in self.actions]

        # get backends from the current user
        backends = Backend.objects.filter(
            memberships__in=self.request.user.backend_memberships.all()
        )
        kwargs["backends"] = backends_to_choices(backends)

        return kwargs

    def get_initial(self):
        # derive will_notify for the JobRequestCreateForm from the Workspace
        # setting as a default for the form which the user can override.
        return {"will_notify": self.workspace.should_notify}

    def get_repo_is_private(self):
        return get_repo_is_private(
            self.workspace.repo_owner,
            self.workspace.repo_name,
        )

    def get_latest_job_request(self):
        return (
            self.workspace.job_requests.prefetch_related("jobs")
            .order_by("-created_at")
            .first()
        )

    def post(self, request, *args, **kwargs):
        if self.workspace.is_archived:
            msg = (
                "You cannot create Jobs for an archived Workspace."
                "Please contact an admin if you need to have it unarchved."
            )
            messages.error(request, msg)
            return redirect(self.workspace)

        return super().post(request, *args, **kwargs)


class WorkspaceLog(ListView):
    paginate_by = 25
    template_name = "workspace_log.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                name=self.kwargs["workspace_slug"],
            )
        except Workspace.DoesNotExist:
            return redirect("/")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_can_run_jobs"] = can_run_jobs(self.request.user)
        context["workspace"] = self.workspace
        return context

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(workspace=self.workspace)
            .prefetch_related("jobs")
            .select_related("workspace")
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

        return qs


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class WorkspaceNotificationsToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        form = WorkspaceNotificationsToggleForm(data=request.POST)
        form.is_valid()

        workspace.should_notify = form.cleaned_data["should_notify"]
        workspace.save()

        return redirect(workspace)


class WorkspaceCurrentOutputsDetail(View):
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
            request.user, "view_release_file", project=workspace.project
        ):
            raise Http404

        context = {
            "files_url": workspace.get_releases_api_url(),
            "prepare_url": workspace.get_create_snapshot_api_url(),
            "workspace": workspace,
        }
        return TemplateResponse(
            request,
            "workspace_current_outputs_detail.html",
            context=context,
        )


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
            request.user, "view_release_file", project=workspace.project
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
