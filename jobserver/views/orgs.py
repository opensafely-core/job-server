from django.db.models import Count
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from ..models import JobRequest, Org


class OrgDetail(DetailView):
    model = Org
    template_name = "org/detail.html"

    def get_context_data(self, **kwargs):
        projects = (
            self.object.projects.annotate(
                member_count=Count("memberships", distinct=True)
            )
            .annotate(
                workspace_count=Count("workspaces", distinct=True),
            )
            .order_by(Lower("name"))
        )

        return super().get_context_data(**kwargs) | {
            "projects": projects,
        }


class OrgEventLog(ListView):
    paginate_by = 25
    template_name = "org/event_log.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = get_object_or_404(Org, slug=self.kwargs["slug"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "org": self.org,
        }

    def get_queryset(self):
        return (
            JobRequest.objects.with_started_at()
            .filter(workspace__project__org=self.org)
            .select_related(
                "backend", "workspace", "workspace__project", "workspace__project__org"
            )
            .order_by("-pk")
        )


class OrgList(ListView):
    queryset = Org.objects.annotate(project_count=Count("projects")).order_by(
        Lower("name")
    )
    template_name = "org/list.html"
