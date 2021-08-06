from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, View

from ..authorization import has_permission
from ..models import Project, Release, ReleaseFile, Snapshot, Workspace
from ..releases import build_outputs_zip, workspace_files


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
        can_delete_files = has_permission(
            self.request.user, "delete_release_file", project=self.project
        )
        return super().get_context_data(**kwargs) | {
            "project": self.project,
            "user_can_delete_files": can_delete_files,
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


class ReleaseFileDelete(View):
    def post(self, request, *args, **kwargs):
        rfile = get_object_or_404(
            ReleaseFile,
            release__workspace__project__org__slug=self.kwargs["org_slug"],
            release__workspace__project__slug=self.kwargs["project_slug"],
            release__workspace__name=self.kwargs["workspace_slug"],
            release__pk=self.kwargs["pk"],
            pk=self.kwargs["release_file_id"],
        )

        if not rfile.absolute_path().exists():
            raise Http404

        if not has_permission(
            request.user,
            "delete_release_file",
            project=rfile.release.workspace.project,
        ):
            raise Http404

        with transaction.atomic():
            # delete file on disk
            rfile.absolute_path().unlink()

            rfile.deleted_by = request.user
            rfile.deleted_at = timezone.now()
            rfile.save()

        return redirect(rfile.release.workspace.get_releases_url())


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


class SnapshotDownload(View):
    def get(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__project__org__slug=self.kwargs["org_slug"],
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not snapshot.files.exists():
            raise Http404

        can_view_unpublished_files = has_permission(
            request.user,
            "view_release_file",
            project=snapshot.workspace.project,
        )
        if snapshot.is_draft and not can_view_unpublished_files:
            raise Http404

        zf = build_outputs_zip(snapshot.files.all())
        return FileResponse(
            zf,
            as_attachment=True,
            filename=f"release-{snapshot.pk}.zip",
        )


class WorkspaceReleaseList(ListView):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not workspace.releases.exists():
            raise Http404

        can_delete_files = has_permission(
            request.user, "delete_release_file", project=workspace.project
        )
        can_view_all_files = has_permission(
            request.user,
            "view_release_file",
            project=workspace.project,
        )

        latest_files = sorted(
            workspace_files(workspace).values(), key=lambda rf: rf.name
        )

        context = {
            "latest_files": latest_files,
            "releases": workspace.releases.order_by("-created_at"),
            "user_can_delete_files": can_delete_files,
            "user_can_view_all_files": can_view_all_files,
            "workspace": workspace,
        }

        return TemplateResponse(
            request,
            "workspace_release_list.html",
            context=context,
        )
