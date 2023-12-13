from csp.decorators import csp_exempt
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import transaction
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import View

from ..authorization import has_permission
from ..models import (
    Project,
    PublishRequest,
    Release,
    ReleaseFile,
    Snapshot,
    Workspace,
)
from ..releases import build_outputs_zip, serve_file, workspace_files
from ..utils import build_spa_base_url


class ProjectReleaseList(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

        releases = (
            Release.objects.filter(workspace__project=project)
            .order_by("-created_at")
            .select_related(
                "created_by",
                "workspace",
                "workspace__project",
            )
            .prefetch_related(
                Prefetch("files", queryset=ReleaseFile.objects.order_by("name"))
            )
        )
        if not releases.exists():
            raise Http404

        can_delete_files = has_permission(
            request.user, "release_file_delete", project=project
        )
        can_view_files = has_permission(
            request.user, "release_file_view", project=project
        )

        releases = [
            {
                "backend": r.backend,
                "can_view_files": can_view_files and r.files.exists(),
                "created_at": r.created_at,
                "created_by": r.created_by,
                "download_url": r.get_download_url(),
                "files": r.files.all(),
                "id": r.pk,
                "view_url": r.get_absolute_url(),
                "workspace": r.workspace,
            }
            for r in releases
        ]

        context = {
            "project": project,
            "releases": releases,
            "user_can_delete_files": can_delete_files,
        }

        return TemplateResponse(
            request,
            "project_release_list.html",
            context=context,
        )


class PublishedSnapshotFile(View):
    def get(self, request, *args, **kwargs):
        """Return the content of a specific ReleaseFile which has been published"""
        rfile = get_object_or_404(ReleaseFile, id=self.kwargs["file_id"])

        is_published = rfile.snapshots.filter(
            publish_requests__decision=PublishRequest.Decisions.APPROVED
        ).exists()
        if not is_published:
            raise Http404

        return serve_file(request, rfile)


class ReleaseDetail(View):
    @csp_exempt
    def get(self, request, *args, **kwargs):
        """
        Orchestrate viewing of a Release in the SPA

        We consume two URLs with one view, because we want to both do
        permissions checks on the Release but also load the SPA for any given
        path under a Release.
        """
        release = get_object_or_404(
            Release,
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not release.files.exists():
            raise Http404

        if not has_permission(
            request.user,
            "release_file_view",
            project=release.workspace.project,
        ):
            raise Http404

        base_path = build_spa_base_url(request.path, self.kwargs.get("path", ""))
        context = {
            "base_path": base_path,
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
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not release.files.exists():
            raise Http404

        if not has_permission(
            request.user,
            "release_file_view",
            project=release.workspace.project,
        ):
            raise Http404

        zf = build_outputs_zip(release.files.all(), request.build_absolute_uri)
        return FileResponse(
            zf,
            as_attachment=True,
            filename=f"release-{release.pk}.zip",
        )


class ReleaseFileDelete(View):
    def post(self, request, *args, **kwargs):
        rfile = get_object_or_404(
            ReleaseFile,
            release__workspace__project__slug=self.kwargs["project_slug"],
            release__workspace__name=self.kwargs["workspace_slug"],
            release__pk=self.kwargs["pk"],
            pk=self.kwargs["release_file_id"],
        )

        if rfile.is_deleted or not rfile.absolute_path().exists():
            raise Http404

        if not has_permission(
            request.user,
            "release_file_delete",
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
    @csp_exempt
    def get(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        has_permission_to_view = has_permission(
            request.user, "release_file_view", project=snapshot.workspace.project
        )
        if snapshot.is_draft and not has_permission_to_view:
            raise Http404

        base_path = build_spa_base_url(request.path, self.kwargs.get("path", ""))
        publish_request = (
            snapshot.publish_requests.exclude(decision=None)
            .filter(decision=PublishRequest.Decisions.APPROVED)
            .order_by("-created_at")
            .first()
        )

        context = {
            "base_path": base_path,
            "files_url": snapshot.get_api_url(),
            "publish_request": publish_request,
            "snapshot": snapshot,
        }

        can_publish = has_permission(
            request.user, "snapshot_publish", project=snapshot.workspace.project
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
            workspace__project__slug=self.kwargs["project_slug"],
            workspace__name=self.kwargs["workspace_slug"],
            pk=self.kwargs["pk"],
        )

        if not snapshot.files.exists():
            raise Http404

        can_view_unpublished_files = has_permission(
            request.user,
            "release_file_view",
            project=snapshot.workspace.project,
        )
        if snapshot.is_draft and not can_view_unpublished_files:
            raise Http404

        zf = build_outputs_zip(snapshot.files.all(), request.build_absolute_uri)
        return FileResponse(
            zf,
            as_attachment=True,
            filename=f"release-{snapshot.pk}.zip",
        )


class WorkspaceReleaseList(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not workspace.releases.exists():
            raise Http404

        can_delete_files = has_permission(
            request.user, "release_file_delete", project=workspace.project
        )
        can_view_files = has_permission(
            request.user,
            "release_file_view",
            project=workspace.project,
        )

        def build_files(files, url_method_name):
            return [
                {
                    "pk": f.pk,
                    "name": f.name,
                    "is_deleted": f.is_deleted,
                    "deleted_at": f.deleted_at,
                    "deleted_by": f.deleted_by,
                    "detail_url": getattr(f, url_method_name),
                    "get_delete_url": f.get_delete_url(),
                }
                for f in files
            ]

        latest_files = list(
            sorted(workspace_files(workspace).values(), key=lambda rf: rf.name)
        )
        latest_release = {
            "can_view_files": can_view_files and bool(latest_files),
            "download_url": workspace.get_latest_outputs_download_url(),
            "files": build_files(latest_files, "get_latest_url"),
            "id": "latest",
            "title": "All outputs - the most recent version of each file",
            "view_url": workspace.get_latest_outputs_url(),
        }

        def build_title(release):
            created_at = naturaltime(release.created_at)
            created_at = (
                f'<span title="{release.created_at.isoformat()}">{created_at}</span>'
            )
            suffix = f" by {release.created_by.name} from {release.backend.name} {created_at}"
            prefix = "Files released" if release.files else "Released"

            return mark_safe(prefix + suffix)

        releases = [
            {
                "can_view_files": can_view_files and r.files.exists(),
                "download_url": r.get_download_url(),
                "files": build_files(r.files.all(), "get_absolute_url"),
                "id": r.pk,
                "title": build_title(r),
                "view_url": r.get_absolute_url(),
            }
            for r in workspace.releases.select_related("backend", "created_by")
            .prefetch_related(
                Prefetch("files", queryset=ReleaseFile.objects.order_by("name"))
            )
            .order_by("-created_at")
        ]

        context = {
            "latest_release": latest_release,
            "releases": releases,
            "user_can_delete_files": can_delete_files,
            "workspace": workspace,
        }

        return TemplateResponse(
            request,
            "workspace_release_list.html",
            context=context,
        )
