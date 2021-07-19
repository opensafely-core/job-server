from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import ListView, View

from ..authorization import has_permission
from ..models import Project, Release, Snapshot, Workspace
from ..releases import workspace_files
from ..utils import set_from_qs


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

        # TODO: check permissions here

        context = {
            "api_url": reverse("api:release", kwargs={"release_id": release.id}),
            "release": release,
        }
        return TemplateResponse(
            request,
            "release_detail.html",
            context=context,
        )


class SnapshotCreate(View):
    def post(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(request.user, "publish_output"):
            raise Http404

        if not workspace.files.exists():
            messages.error(
                request,
                "There are no outputs to publish for this workspace.",
            )
            return redirect(workspace)

        file_ids = {f.pk for f in workspace_files(workspace).values()}
        snapshot_ids = [set_from_qs(pr.files.all()) for pr in workspace.snapshots.all()]
        if file_ids in snapshot_ids:
            messages.error(
                request,
                "A release with the current files already exists, please use that one.",
            )
            return redirect(workspace)

        snapshot = workspace.snapshots.create(created_by=request.user)
        snapshot.files.set(workspace.files.all())

        return redirect(workspace)


class SnapshotDetail(View):
    def get(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__project__org__slug=self.kwargs["org_slug"],
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not has_permission(
            request.user, "view_release_file", project=snapshot.workspace.project
        ):
            raise Http404

        context = {
            "api_url": snapshot.get_api_url(),
            "snapshot": snapshot,
        }
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
