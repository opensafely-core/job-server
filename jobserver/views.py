from django.views.generic import ListView

from .api.models import Job


class JobList(ListView):
    paginate_by = 25
    queryset = Job.objects.select_related("workspace")
    template_name = "job_list.html"
