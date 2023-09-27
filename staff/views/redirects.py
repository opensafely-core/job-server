from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from redirects.models import Redirect

from .qwargs_tools import qwargs


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RedirectDelete(View):
    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Redirect, pk=self.kwargs["pk"])

        obj.delete()

        messages.success(request, f"Deleted redirect for {obj.type}: {obj.obj.name}")

        return redirect("staff:redirect-list")


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RedirectDetail(DetailView):
    model = Redirect
    template_name = "staff/redirect/detail.html"


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RedirectList(ListView):
    model = Redirect
    ordering = "-old_url"
    paginate_by = 25
    template_name = "staff/redirect/list.html"

    def get_context_data(self, **kwargs):
        types = [
            {"name": f.name.replace("_", " "), "value": f.name.lower()}
            for f in Redirect.targets()
        ]
        return super().get_context_data(**kwargs) | {
            "types": types,
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = super().get_queryset()

        if q := self.request.GET.get("q"):
            fields = [
                "analysis_request__title",
                "created_by__fullname",
                "created_by__username",
                "old_url",
                "org__name",
                "project__name",
                "workspace__name",
            ]
            qs = qs.filter(qwargs(fields, q))

        if object_type := self.request.GET.get("type"):
            qs = qs.filter(**{f"{object_type}__isnull": False})

        return qs.distinct()
