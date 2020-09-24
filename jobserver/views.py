from django.views.generic import DetailView, ListView

from .api.models import Job


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobList(ListView):
    paginate_by = 25
    queryset = Job.objects.select_related("workspace")
    template_name = "job_list.html"
