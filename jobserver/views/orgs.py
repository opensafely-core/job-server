from django.db.models import Count
from django.db.models.functions import Lower
from django.views.generic import DetailView, ListView

from ..models import Org


class OrgDetail(DetailView):
    model = Org
    template_name = "org_detail.html"

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


class OrgList(ListView):
    queryset = Org.objects.annotate(project_count=Count("projects")).order_by(
        Lower("name")
    )
    template_name = "org_list.html"
