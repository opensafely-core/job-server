from django.views.generic import TemplateView

from ..models import JobRequest, Workspace


class Index(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        job_requests = JobRequest.objects.select_related(
            "created_by", "workspace", "workspace__project", "workspace__project__org"
        ).order_by("-created_at")

        if not self.request.user.is_authenticated:
            return super().get_context_data(**kwargs) | {
                "all_job_requests": job_requests[:10],
            }

        analysis_requests = self.request.user.analysis_requests.select_related(
            "project", "project__org"
        ).order_by("-created_at")

        applications = self.request.user.applications.order_by("-created_at")

        projects = [
            {
                "name": m.project.title,
                "url": m.project.get_absolute_url(),
            }
            for m in self.request.user.project_memberships.select_related(
                "project", "project__org"
            ).order_by("-created_at")[:5]
        ]

        user_job_requests = job_requests.filter(created_by=self.request.user)

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
            "all_job_requests": job_requests[:10],
            "analysis_requests": analysis_requests[:5],
            "applications": applications[:5],
            "counts": counts,
            "job_requests": user_job_requests[:5],
            "projects": projects,
            "workspaces": workspaces[:5],
        }
