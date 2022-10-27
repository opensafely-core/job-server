from django.db.models import Count, Min
from django.db.models.functions import Least
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Project


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class Copiloting(TemplateView):
    template_name = "staff/dashboards/copiloting.html"

    def get_context_data(self, **kwargs):
        projects = (
            Project.objects.select_related("copilot", "org")
            .annotate(
                workspace_count=Count("workspaces", distinct=True),
                job_request_count=Count("workspaces__job_requests", distinct=True),
                files_released_count=Count("workspaces__files", distinct=True),
                date_first_run=Min(
                    Least(
                        "workspaces__job_requests__jobs__started_at",
                        "workspaces__job_requests__jobs__created_at",
                    )
                ),
            )
            .order_by("name")
        )

        return super().get_context_data(**kwargs) | {
            "projects": projects,
        }
