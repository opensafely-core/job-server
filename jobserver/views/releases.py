from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import ListView, View

from ..authorization import has_permission
from ..models import Project, Release, Snapshot, Workspace
from ..releases import build_outputs_zip


class ProjectReleaseList(ListView):
    template_name = "project_release_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "project": self.project,
        }

    def get_queryset(self):
        return (
            Release.objects.filter(workspace__project=self.project)
            .order_by("-created_at")
            .select_related("workspace")
        )


class ReleaseDetail(View):
    def get(self, request, *args, **kwargs):
        """
        Orchestrate viewing of a Release in the SPA

        We consume two URLs with one view, because we want to both do
        permissions checks on the Release but also load the SPA for any given
        path under a Release.
        """
        release = get_object_or_404(
            Release,
            workspace__project__org__slug=self.kwargs["org_slug"],
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not release.files.exists():
            raise Http404

        # TODO: check permissions here

        context = {
            "files_url": reverse("api:release", kwargs={"release_id": release.id}),
            "release": release,
        }
        return TemplateResponse(
            request,
            "release_detail.html",
            context=context,
        )


class ReleaseDownload(View):
    def get(self, request, *args, **kwargs):
        release = get_object_or_404(
            Release,
            workspace__project__org__slug=self.kwargs["org_slug"],
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not release.files.exists():
            raise Http404

        if not has_permission(
            request.user,
            "view_release_file",
            project=release.workspace.project,
        ):
            raise Http404

        zf = build_outputs_zip(release.files.all())
        return FileResponse(
            zf,
            as_attachment=True,
            filename=f"release-{release.pk}.zip",
        )


class SnapshotDetail(View):
    def get(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__project__org__slug=self.kwargs["org_slug"],
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        has_permission_to_view = has_permission(
            request.user, "view_release_file", project=snapshot.workspace.project
        )
        if snapshot.is_draft and not has_permission_to_view:
            raise Http404

        context = {
            "files_url": snapshot.get_api_url(),
            "snapshot": snapshot,
        }

        can_publish = has_permission(
            request.user, "publish_output", project=snapshot.workspace.project
        )
        if can_publish and snapshot.is_draft:
            context["publish_url"] = snapshot.get_publish_api_url()

        return TemplateResponse(
            request,
            "snapshot_detail.html",
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
        return super().get_context_data(**kwargs) | {
            "workspace": self.workspace,
        }

    def get_queryset(self):
        return self.workspace.releases.order_by("-created_at")
