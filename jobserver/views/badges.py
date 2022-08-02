from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from pybadges import badge

from ..models import Job, ReleaseFile, Workspace


class WorkspaceNumJobs(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        num_jobs = Job.objects.filter(job_request__workspace=workspace).count()

        s = badge(
            left_text="Jobs run",
            right_text=str(num_jobs),
            right_color="#0058be",
        )
        return HttpResponse(s, headers={"Content-Type": "image/svg+xml"})


class WorkspaceNumPublished(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        num_published = (
            ReleaseFile.objects.filter(snapshots__workspace=workspace)
            .distinct()
            .count()
        )

        s = badge(
            left_text="Published outputs",
            right_text=str(num_published),
            right_color="#0058be",
        )
        return HttpResponse(s, headers={"Content-Type": "image/svg+xml"})


class WorkspaceNumReleased(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        num_released = ReleaseFile.objects.filter(release__workspace=workspace).count()

        s = badge(
            left_text="Released outputs",
            right_text=str(num_released),
            right_color="#0058be",
        )
        return HttpResponse(s, headers={"Content-Type": "image/svg+xml"})
