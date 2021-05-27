from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, View

from ..authorization import SuperUser, has_permission, has_role
from ..backends import backends_to_choices
from ..forms import (
    JobRequestCreateForm,
    WorkspaceArchiveToggleForm,
    WorkspaceCreateForm,
    WorkspaceNotificationsToggleForm,
)
from ..github import get_branch_sha, get_repos_with_branches
from ..models import Backend, JobRequest, Workspace
from ..project import get_actions, get_project, load_yaml
from ..roles import can_run_jobs


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class WorkspaceArchiveToggle(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(Workspace, name=self.kwargs["name"])

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
        gh_org = self.request.user.orgs.first().github_orgs[0]
        self.repos_with_branches = sorted(
            get_repos_with_branches(gh_org), key=lambda r: r["name"].lower()
        )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        instance.save()

        return redirect(instance)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repos_with_branches"] = self.repos_with_branches
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["repos_with_branches"] = self.repos_with_branches
        return kwargs


class BaseWorkspaceDetail(CreateView):
    """
    WorkspaceDetail base view

    Handles everything for the WorkspaceDetail page except Workspace permission
    lookups.  Any subclass must implement the can_run_jobs method, returning a
    boolean.
    """

    form_class = JobRequestCreateForm
    model = JobRequest
    template_name = "workspace_detail.html"

    def can_run_jobs(self, user):
        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        self.user_can_run_jobs = self.can_run_jobs(request.user)

        self.show_details = (
            request.user.is_authenticated
            and self.user_can_run_jobs
            and not self.workspace.is_archived
        )

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

        if has_role(self.request.user, SuperUser):
            # Use the form data to decide which backend to use for superusers.
            backend = Backend.objects.get(name=form.cleaned_data.pop("backend"))
        else:
            # For non-superusers we're only exposing one backend currently.
            backend = Backend.objects.get(name="tpp")

        backend.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            project_definition=self.project,
            **form.cleaned_data,
        )
        return redirect("workspace-logs", name=self.workspace.name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.actions
        context["branch"] = self.workspace.branch
        context["latest_job_request"] = self.get_latest_job_request()
        context["is_superuser"] = has_role(self.request.user, SuperUser)
        context["show_details"] = self.show_details
        context["user_can_run_jobs"] = self.user_can_run_jobs
        context["workspace"] = self.workspace
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actions"] = [a["name"] for a in self.actions]

        if has_role(self.request.user, SuperUser):
            # TODO: move to ModelForm declaration once all users can pick backends
            backends = Backend.objects.all()
            backend_choices = backends_to_choices(backends)
            kwargs["backends"] = backend_choices

        return kwargs

    def get_initial(self):
        # derive will_notify for the JobRequestCreateForm from the Workspace
        # setting as a default for the form which the user can override.
        return {"will_notify": self.workspace.should_notify}

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


class GlobalWorkspaceDetail(BaseWorkspaceDetail):
    def can_run_jobs(self, user):
        return can_run_jobs(user)

    def dispatch(self, request, *args, **kwargs):
        if "project_slug" in self.kwargs:
            return redirect(
                "project-workspace-detail",
                org_slug=self.kwargs["org_slug"],
                project_slug=self.kwargs["project_slug"],
                workspace_slug=self.kwargs["workspace_slug"],
            )

        try:
            self.workspace = Workspace.objects.get(name=self.kwargs["name"])
        except Workspace.DoesNotExist:
            return redirect("/")

        return super().dispatch(request, *args, **kwargs)


class ProjectWorkspaceDetail(BaseWorkspaceDetail):
    def can_run_jobs(self, user):
        return has_permission(user, "run_job", project=self.workspace.project)

    def dispatch(self, request, *args, **kwargs):
        if "project_slug" not in self.kwargs:
            return redirect("workspace-detail", name=self.kwargs["name"])

        try:
            self.workspace = Workspace.objects.get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                name=self.kwargs["workspace_slug"],
            )
        except Workspace.DoesNotExist:
            return redirect("/")

        return super().dispatch(request, *args, **kwargs)


class WorkspaceLog(ListView):
    paginate_by = 25
    template_name = "workspace_log.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(name=self.kwargs["name"])
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
        workspace = get_object_or_404(Workspace, name=self.kwargs["name"])

        form = WorkspaceNotificationsToggleForm(data=request.POST)
        form.is_valid()

        workspace.should_notify = form.cleaned_data["should_notify"]
        workspace.save()

        return redirect(workspace)


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class WorkspaceReleaseView(View):
    def get(self, request, name, release):
        return f"release page for {name}/{release}"  # pragma: no cover
