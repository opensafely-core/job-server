from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, TemplateView, View

from .backends import show_warning
from .forms import JobRequestCreateForm, WorkspaceCreateForm
from .github import get_branch_sha, get_repos_with_branches
from .models import Backend, Job, JobRequest, Stats, User, Workspace
from .project import get_actions


def filter_by_status(job_requests, status):
    """
    Filter JobRequests by status property

    JobRequest.status is built by "bubbling up" the status of each related Job.
    However, the construction of that property isn't easily converted to a
    QuerySet, hence this function.
    """
    if not status:
        return job_requests

    status_lut = {
        "failed": lambda r: r.status.lower() == "failed",
        "running": lambda r: r.status.lower() == "running",
        "pending": lambda r: r.status.lower() == "pending",
        "succeeded": lambda r: r.status.lower() == "succeeded",
    }
    func = status_lut[status]
    return list(filter(func, job_requests))


def superuser_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return f(request, *args, **kwargs)

        messages.error(request, "Only admins can view Backends.")
        return redirect("/")

    return wrapper


@method_decorator(superuser_required, name="dispatch")
class BackendDetail(DetailView):
    model = Backend
    template_name = "backend_detail.html"


@method_decorator(superuser_required, name="dispatch")
class BackendList(ListView):
    model = Backend
    template_name = "backend_list.html"


@method_decorator(superuser_required, name="dispatch")
class BackendRotateToken(View):
    def post(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, pk=self.kwargs["pk"])

        backend.rotate_token()

        return redirect(backend)


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        job_requests = JobRequest.objects.prefetch_related("jobs").order_by(
            "-created_at"
        )[:5]
        workspaces = Workspace.objects.order_by("name")

        context = super().get_context_data(**kwargs)
        context["job_requests"] = job_requests
        context["workspaces"] = workspaces
        return context


class JobDetail(DetailView):
    model = Job
    slug_field = "identifier"
    slug_url_kwarg = "identifier"
    template_name = "job_detail.html"


class JobZombify(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Only admins can zombify Jobs.")
            return redirect("job-detail", identifier=self.kwargs["identifier"])

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(Job, identifier=self.kwargs["identifier"])

        job.status = "failed"
        job.status_message = "Job manually zombified"
        job.save()

        return redirect(job)


class JobRequestDetail(DetailView):
    model = JobRequest
    queryset = JobRequest.objects.select_related("workspace").prefetch_related("jobs")
    template_name = "job_request_detail.html"


class JobRequestList(ListView):
    paginate_by = 25
    template_name = "job_request_list.html"

    def get_context_data(self, **kwargs):
        # only get Users created via GitHub OAuth
        users = User.objects.exclude(social_auth=None)
        users = sorted(users, key=lambda u: u.name.lower())

        # filter object list based on status arg
        filtered_object_list = filter_by_status(
            self.object_list, self.request.GET.get("status")
        )
        context = super().get_context_data(object_list=filtered_object_list, **kwargs)

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
                qs = qs.filter(jobs__action__icontains=q)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(Q(jobs__action__icontains=q) | Q(jobs__pk=q))

        username = self.request.GET.get("username")
        if username:
            qs = qs.filter(created_by__username=username)

        workspace = self.request.GET.get("workspace")
        if workspace:
            qs = qs.filter(workspace_id=workspace)

        return qs


class JobRequestZombify(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Only admins can zombify Jobs.")
            return redirect("job-request-detail", pk=self.kwargs["pk"])

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        job_request = get_object_or_404(JobRequest, pk=self.kwargs["pk"])

        job_request.jobs.update(
            status="failed", status_message="Job manually zombified"
        )

        return redirect("job-request-detail", pk=job_request.pk)


class Status(View):
    def get(self, request, *args, **kwargs):
        acked = JobRequest.objects.acked().count()
        unacked = JobRequest.objects.unacked().count()

        try:
            last_seen = Stats.objects.first().api_last_seen
        except AttributeError:
            last_seen = None

        def format_last_seen(last_seen):
            if last_seen is None:
                return "never"

            return last_seen.strftime("%Y-%m-%d %H:%M:%S")

        context = {
            "backends": [
                {
                    "name": "TPP",
                    "last_seen": format_last_seen(last_seen),
                    "queue": {
                        "acked": acked,
                        "unacked": unacked,
                    },
                    "show_warning": show_warning(unacked, last_seen),
                },
            ],
        }

        return TemplateResponse(request, "status.html", context)


@method_decorator(login_required, name="dispatch")
class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.repos_with_branches = sorted(
            get_repos_with_branches(), key=lambda r: r["name"].lower()
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


class WorkspaceDetail(CreateView):
    form_class = JobRequestCreateForm
    model = JobRequest
    template_name = "workspace_detail.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(name=self.kwargs["name"])
        except Workspace.DoesNotExist:
            return redirect("/")

        if not request.user.is_authenticated:
            # short-circuit for logged out users to avoid the hop to grab
            # actions from GitHub
            self.actions = []
            return super().dispatch(request, *args, **kwargs)

        action_status_lut = self.workspace.get_action_status_lut()

        # build actions as list or render the exception to the page
        try:
            self.actions = list(
                get_actions(
                    self.workspace.repo_name,
                    self.workspace.branch,
                    action_status_lut,
                )
            )
        except Exception as e:
            self.actions = []
            # this is a bit nasty, need to mirror what get/post would set up for us
            self.object = None
            context = self.get_context_data(actions_error=str(e))
            return self.render_to_response(context=context)

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        sha = get_branch_sha(self.workspace.repo_name, self.workspace.branch)

        # Pick a backend.
        # We're only configuring one backend in an installation currently. Rely
        # on that for now.
        # TODO: use the form data to decide which backend to use here when the
        # form exposes backends
        TPP = Backend.objects.get(name="tpp")

        TPP.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            **form.cleaned_data,
        )
        return redirect("workspace-logs", name=self.workspace.name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.actions
        context["branch"] = self.workspace.branch
        context["workspace"] = self.workspace
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actions"] = [a["name"] for a in self.actions]
        return kwargs


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
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(jobs__action__icontains=q)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(Q(jobs__action__icontains=q) | Q(jobs__pk=q))

        return qs
