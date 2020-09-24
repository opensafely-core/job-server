from django.views.generic import DetailView, ListView

from .api.models import Job, Workspace


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobList(ListView):
    paginate_by = 25
    queryset = Job.objects.select_related("workspace")
    template_name = "job_list.html"


class WorkspaceList(ListView):
    paginate_by = 25
    queryset = Workspace.objects.prefetch_related("jobs")
    template_name = "workspace_list.html"
