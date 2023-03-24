from django.views.generic import TemplateView

from ..models import JobRequest, Workspace


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        job_requests = JobRequest.objects.select_related(
            "workspace", "workspace__project", "workspace__project__org"
        ).order_by("-created_at")[:5]
        workspaces = (
            Workspace.objects.filter(
                is_archived=False, project__in=self.request.user.projects.all()
            )
            .select_related("project", "project__org")
            .order_by("-created_at")
        )

        counts = {
            "applications": self.request.user.applications.count(),
            "job_requests": self.request.user.job_requests.count(),
            "projects": self.request.user.project_memberships.count(),
            "workspaces": workspaces.count(),
        }

        return super().get_context_data(**kwargs) | {
            "counts": counts,
            "job_requests": job_requests,
            "workspaces": workspaces,
        }
