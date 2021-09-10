from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import Org


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgDetail(DetailView):
    model = Org
    template_name = "staff/org_detail.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "members": self.object.members.order_by("username"),
            "projects": self.object.projects.order_by("name"),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgEdit(UpdateView):
    fields = [
        "name",
    ]
    model = Org
    template_name = "staff/org_edit.html"

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class OrgList(ListView):
    queryset = Org.objects.order_by("name")
    template_name = "staff/org_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)

        return qs
