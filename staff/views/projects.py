from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Org, Project


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectDetail(DetailView):
    model = Project
    template_name = "staff/project_detail.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "workspaces": self.object.workspaces.order_by("name"),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectEdit(UpdateView):
    fields = ["uses_new_release_flow"]
    model = Project
    template_name = "staff/project_edit.html"

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ProjectList(ListView):
    queryset = Project.objects.select_related("org").order_by("name")
    template_name = "staff/project_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "orgs": Org.objects.order_by("name"),
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)

        org = self.request.GET.get("org")
        if org:
            qs = qs.filter(org__slug=org)
        return qs
