from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from interactive.models import AnalysisRequest
from jobserver.models import Project, Workspace


@method_decorator(login_required, name="dispatch")
class AnalysisRequestList(ListView):
    model = AnalysisRequest
    template_name = "yours/analysis_request_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(created_by=self.request.user)
            .select_related("project", "project__org")
        )


@method_decorator(login_required, name="dispatch")
class ProjectList(ListView):
    model = Project
    template_name = "yours/project_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(pk__in=self.request.user.projects.values_list("pk"))
            .select_related("org")
        )


@method_decorator(login_required, name="dispatch")
class WorkspaceList(ListView):
    model = Workspace
    template_name = "yours/workspace_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(project__in=self.request.user.projects.all())
            .select_related("project", "project__org")
        )
