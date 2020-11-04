import operator

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from .forms import JobRequestCreateForm, WorkspaceCreateForm
from .github import get_branch_sha, get_repos_with_branches
from .models import Job, JobRequest, User, Workspace
from .project import get_actions


def filter_by_status(job_requests, status):
    """
    Filter JobRequests by possible status

    Status is currently inferred from various Job fields and "bubbled up"
    to a JobRequest.  This converts the view's QuerySet to a list via a
    filter which uses properties on JobRequest to cut down the values to
    those requested.

    TODO: replace with a custom QuerySet once status is driven entirely via
    the job-runner
    """
    if not status:
        return job_requests

    status_lut = {
        "failed": lambda r: r.is_failed,
        "running": lambda r: r.is_running,
        "pending": lambda r: r.is_pending,
        "succeeded": lambda r: r.is_succeeded,
    }
    func = status_lut[status]
    return list(filter(func, job_requests))


class Dashboard(ListView):
    """
    User-centric Jobs List

    This is a barely-modified version of JobRequestList for now, but is
    expected to grow more User-centric features.
    """

    paginate_by = 25
    template_name = "dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("job-list")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # FIXME: This is a hack, see filter_by_status docstring for why and
        # when to remove it
        context["object_list"] = filter_by_status(
            self.object_list, self.request.GET.get("status")
        )

        context["statuses"] = ["failed", "running", "pending", "succeeded"]
        context["workspaces"] = Workspace.objects.all()
        return context

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(created_by=self.request.user)
            .prefetch_related("jobs")
            .select_related("workspace")
            .order_by("-pk")
        )

        q = self.request.GET.get("q")
        if q:
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(jobs__action_id__icontains=q)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(Q(jobs__action_id__icontains=q) | Q(jobs__pk=q))

        workspace = self.request.GET.get("workspace")
        if workspace:
            qs = qs.filter(workspace_id=workspace)

        return qs


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobRequestDetail(DetailView):
    model = JobRequest
    queryset = JobRequest.objects.select_related("workspace").prefetch_related("jobs")
    template_name = "job_request_detail.html"


class JobRequestList(ListView):
    paginate_by = 25
    template_name = "jobrequest_list.html"

    def get_context_data(self, **kwargs):
        # only get Users created via GitHub OAuth
        users = User.objects.exclude(social_auth=None)
        users = sorted(users, key=lambda u: u.name.lower())

        context = super().get_context_data(**kwargs)

        # FIXME: This is a hack, see filter_by_status docstring for why and
        # when to remove it
        context["object_list"] = filter_by_status(
            self.object_list, self.request.GET.get("status")
        )

        context["statuses"] = ["failed", "running", "pending", "succeeded"]
        context["users"] = {u.username: u.name for u in users}
        context["workspaces"] = Workspace.objects.all()
        return context

    def get_queryset(self):
        qs = (
            JobRequest.objects.prefetch_related("jobs")
            .select_related("workspace")
            .order_by("-pk")
        )

        q = self.request.GET.get("q")
        if q:
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(jobs__action_id__icontains=q)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(Q(jobs__action_id__icontains=q) | Q(jobs__pk=q))

        username = self.request.GET.get("username")
        if username:
            qs = qs.filter(created_by__username=username)

        workspace = self.request.GET.get("workspace")
        if workspace:
            qs = qs.filter(workspace_id=workspace)

        return qs


@method_decorator(login_required, name="dispatch")
class JobRequestCreate(CreateView):
    form_class = JobRequestCreateForm
    model = JobRequest
    success_url = "job-list"
    template_name = "job_request_create.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.prefetch_related(
                "job_requests__jobs"
            ).get(pk=self.kwargs["pk"])
        except Workspace.DoesNotExist:
            messages.error(request, "Unknown Workspace, please pick a valid one")
            return redirect("job-select-workspace")

        # build up a list of actions with current statuses from the Workspace's
        # project.yaml for the User to pick from
        actions = get_actions(self.workspace.repo_name, self.workspace.branch)

        actions_with_statues = []
        for action in actions:
            status = self.workspace.get_latest_status_for_action(action["name"])
            actions_with_statues.append(action | {"status": status})

        self.actions = sorted(actions_with_statues, key=operator.itemgetter("name"))

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        sha = get_branch_sha(self.workspace.repo_name, self.workspace.branch)

        job_request = JobRequest.objects.create(
            workspace=self.workspace,
            created_by=self.request.user,
            backend=JobRequest.TPP,
            sha=sha,
            **form.cleaned_data,
        )
        for action in job_request.requested_actions:
            job_request.jobs.create(
                action_id=action,
                force_run=job_request.force_run,
            )

        return redirect("job-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.actions
        context["branch"] = self.workspace.branch
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actions"] = [a["name"] for a in self.actions]
        return kwargs


@method_decorator(login_required, name="dispatch")
class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        instance.save()

        return redirect(instance)

    def get_form_kwargs(self):
        repos_with_branches = sorted(
            get_repos_with_branches(), key=lambda r: r["name"].lower()
        )

        kwargs = super().get_form_kwargs()
        kwargs["repos_with_branches"] = repos_with_branches
        return kwargs


class WorkspaceDetail(DetailView):
    model = Workspace
    template_name = "workspace_detail.html"


class WorkspaceList(ListView):
    ordering = "name"
    paginate_by = 25
    queryset = Workspace.objects.prefetch_related("jobs")
    template_name = "workspace_list.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # if there are no workspaces redirect the user to the new Workspace
        # page immediately
        if request.user.is_authenticated and not self.object_list:
            return redirect("workspace-create")

        return response


@method_decorator(login_required, name="dispatch")
class WorkspaceSelectOrCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_select.html"

    def dispatch(self, request, *args, **kwargs):
        self.repos_with_branches = sorted(
            get_repos_with_branches(), key=lambda r: r["name"].lower()
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repos_with_branches"] = self.repos_with_branches
        context["workspace_list"] = Workspace.objects.order_by("name")
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user
        instance.save()
        return redirect("job-create", pk=instance.pk)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["repos_with_branches"] = self.repos_with_branches
        return kwargs

    def get_success_url(self):
        return reverse("job-create", kwargs={"pk": self.object.pk})
