from django.views.generic import TemplateView

from ..models import JobRequest, Workspace
from ..roles import can_run_jobs


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        job_requests = JobRequest.objects.prefetch_related("jobs").order_by(
            "-created_at"
        )[:5]
        workspaces = (
            Workspace.objects.filter(is_archived=False)
            .select_related("project", "project__org")
            .order_by("name")
        )

        context = super().get_context_data(**kwargs)
        context["job_requests"] = job_requests
        context["user_can_run_jobs"] = can_run_jobs(self.request.user)
        context["workspaces"] = workspaces
        return context
