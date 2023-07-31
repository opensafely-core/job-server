from django.template.response import TemplateResponse
from django.views.generic import View

from ..models import JobRequest, Workspace


class Index(View):
    def get(self, request, *args, **kwargs):
        job_requests = (
            JobRequest.objects.with_started_at()
            .select_related(
                "created_by",
                "workspace",
                "workspace__project",
            )
            .order_by("-created_at")
        )

        if not self.request.user.is_authenticated:
            return TemplateResponse(
                request,
                template="index-unauthenticated.html",
                context={
                    "all_job_requests": job_requests[:10],
                },
            )

        analysis_requests = self.request.user.analysis_requests.select_related(
            "project"
        ).order_by("-created_at")

        applications = self.request.user.applications.order_by("-created_at")

        projects = [
            {
                "name": m.project.title,
                "url": m.project.get_absolute_url(),
            }
            for m in self.request.user.project_memberships.select_related(
                "project"
            ).order_by("-created_at")[:5]
        ]

        user_job_requests = job_requests.filter(created_by=self.request.user)

        workspaces = (
            Workspace.objects.filter(
                is_archived=False, project__in=self.request.user.projects.all()
            )
            .select_related("project")
            .order_by("-created_at")
        )

        counts = {
            "applications": self.request.user.applications.count(),
            "job_requests": self.request.user.job_requests.count(),
            "projects": self.request.user.project_memberships.count(),
            "workspaces": workspaces.count(),
        }

        context = {
            "all_job_requests": job_requests[:10],
            "analysis_requests": analysis_requests[:5],
            "applications": applications[:5],
            "counts": counts,
            "job_requests": user_job_requests[:5],
            "projects": projects,
            "workspaces": workspaces[:5],
        }
        return TemplateResponse(
            request,
            template="index-authenticated.html",
            context=context,
        )
