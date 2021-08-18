from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Workspace


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class WorkspaceDetail(DetailView):
    model = Workspace
    slug_field = "name"
    template_name = "staff/workspace_detail.html"


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class WorkspaceList(ListView):
    model = Workspace
    ordering = "name"
    template_name = "staff/workspace_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(repo__icontains=q))

        return qs
