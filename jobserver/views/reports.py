from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView

from interactive.models import AnalysisRequest

from ..authorization import has_permission
from ..github import _get_github_api
from ..issues import create_copilot_publish_report_request
from ..models import PublishRequest
from ..slacks import notify_copilots_of_publish_request


class PublishRequestCreate(CreateView):
    fields = []
    get_github_api = staticmethod(_get_github_api)
    model = PublishRequest
    template_name = "interactive/publish_request_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.analysis_request = get_object_or_404(
            AnalysisRequest,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            slug=self.kwargs["slug"],
        )

        if not has_permission(
            self.request.user,
            "analysis_request_view",
            project=self.analysis_request.project,
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        publish_request = PublishRequest.create_from_report(
            report=self.analysis_request.report, user=self.request.user
        )

        issue_url = create_copilot_publish_report_request(
            self.analysis_request.report,
            github_api=self.get_github_api(),
        )
        notify_copilots_of_publish_request(
            publish_request,
            self.analysis_request.report,
            issue_url,
        )

        messages.success(
            self.request, "Your request to publish this report was successfully sent"
        )

        return redirect(self.analysis_request)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "analysis_request": self.analysis_request,
        }
