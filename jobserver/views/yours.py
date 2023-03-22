from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from interactive.models import AnalysisRequest


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
