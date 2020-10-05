from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from .forms import JobCreateForm, WorkspaceCreateForm
from .models import Job, JobRequest, Workspace


@method_decorator(login_required, name="dispatch")
class JobCreate(CreateView):
    form_class = JobCreateForm
    model = Job
    template_name = "job_create.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobList(ListView):
    ordering = "-pk"
    paginate_by = 25
    template_name = "job_list.html"

    def filter_by_status(self):
        """
        Filter JobRequests by possible status

        Status is currently inferred from various Job fields and "bubbled up"
        to a JobRequest.  This converts the view's QuerySet to a list via a
        filter which uses properties on JobRequest to cut down the values to
        those requested.

        TODO: replace with a custom QuerySet once status is driven entirely via
        the job-runner
        """
        status = self.request.GET.get("status")

        if not status:
            return self.object_list

        status_lut = {
            "completed": lambda r: r.is_complete,
            "failed": lambda r: r.is_failed,
            "in-progress": lambda r: r.is_in_progress,
            "pending": lambda r: r.is_pending,
        }
        func = status_lut[status]
        return list(filter(func, self.object_list))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # FIXME: This is a hack, see filter_by_status docstring for why and
        # when to remove it
        context["object_list"] = self.filter_by_status()

        context["statuses"] = ["completed", "failed", "in-progress", "pending"]
        context["workspaces"] = Workspace.objects.all()
        return context

    def get_queryset(self):
        qs = JobRequest.objects.prefetch_related("jobs").select_related("workspace")

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


@method_decorator(login_required, name="dispatch")
class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


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
