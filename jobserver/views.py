from django.views.generic import CreateView, DetailView, ListView

from .api.models import Job, Workspace
from .forms import WorkspaceCreateForm


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobList(ListView):
    paginate_by = 25
    template_name = "job_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = ["completed", "in-progress", "pending"]
        context["workspaces"] = Workspace.objects.all()
        return context

    def get_queryset(self):
        qs = Job.objects.select_related("workspace")

        status = self.request.GET.get("status")
        if status:
            status_lut = {
                "completed": qs.completed,
                "in-progress": qs.in_progress,
                "pending": qs.pending,
            }
            qs = status_lut[status]()

        workspace = self.request.GET.get("workspace")
        if workspace:
            qs = qs.filter(workspace_id=workspace)

        return qs


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
    paginate_by = 25
    queryset = Workspace.objects.prefetch_related("jobs")
    template_name = "workspace_list.html"
