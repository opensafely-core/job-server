from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from applications.models import Application
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationDetail(DetailView):
    model = Application
    template_name = "staff/application_detail.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "researchers": self.object.researcher_registrations.order_by("created_at"),
        }


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationList(ListView):
    model = Application
    ordering = "-created_at"
    template_name = "staff/application_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(created_by__first_name__icontains=q)
                | Q(created_by__last_name__icontains=q)
                | Q(created_by__username__icontains=q)
            )

        return qs
