from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView

from interactive.models import AnalysisRequest
from jobserver.authorization import has_permission

from ..models import ReportPublishRequest


class ReportPublishRequestCreate(CreateView):
    fields = []
    model = ReportPublishRequest
    template_name = "interactive/report_publish_request_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.analysis_request = get_object_or_404(
            AnalysisRequest,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            slug=self.kwargs["slug"],
        )

        if self.analysis_request.publish_request:
            messages.error(request, "A request to publish this report already exists")
            return redirect(self.analysis_request)

        if not has_permission(
            self.request.user,
            "analysis_request_view",
            project=self.analysis_request.project,
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ReportPublishRequest.create_from_report(
            report=self.analysis_request.report, user=self.request.user
        )

        # TODO: message a slack somewhere

        messages.success(
            self.request, "Your request to publish this report was successfully sent"
        )

        return redirect(self.analysis_request)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "analysis_request": self.analysis_request,
        }


class ReportPublishRequestUpdate(UpdateView):
    """
    This exists for testing locally/the walking skeleton

    We're not quite sure what form modifying and working with a
    ReportPublishRequest will take yet.
    """

    fields = []
    model = ReportPublishRequest
    template_name = "interactive/report_publish_request_update.html"

    def form_valid(self, form):
        self.object.approve(user=self.request.user)
        # TODO: redirect to the analysis request when we're not testing
        # return redirect(self.object.analysis_request)
        return redirect(self.object)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "project": self.object.report.analysis_request.project,
        }
