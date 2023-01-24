from django.views.generic import TemplateView

from ..models import JobRequest, Workspace


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        job_requests = JobRequest.objects.select_related(
            "workspace", "workspace__project", "workspace__project__org"
        ).order_by("-created_at")[:5]
        workspaces = (
            Workspace.objects.filter(is_archived=False)
            .select_related("project", "project__org", "repo")
            .order_by("name")
        )

        return super().get_context_data(**kwargs) | {
            "job_requests": job_requests,
            "workspaces": workspaces,
        }
