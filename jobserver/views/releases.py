from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import ListView, View

from ..models import Project, Workspace


class Releases(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

        # TODO: check ACL and build signed URLs here

        context = {
            "project": project,
        }
        return TemplateResponse(
            request,
            "project_releases.html",
            context=context,
        )


class WorkspaceReleaseList(ListView):
    template_name = "workspace_release_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        files = sorted(self.workspace.latest_files(), key=lambda file: file.name)

        return super().get_context_data(**kwargs) | {
            "files": files,
            "workspace": self.workspace,
        }

    def get_queryset(self):
        return self.workspace.releases.order_by("-created_at")
