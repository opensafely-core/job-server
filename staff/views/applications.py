from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View

from applications.form_specs import form_specs
from applications.models import Application
from applications.wizard import Wizard
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationDetail(View):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=self.kwargs["pk"])
        wizard = Wizard(application, form_specs)
        pages = [page.review_context() for page in wizard.get_pages()]

        ctx = {
            "researchers": application.researcher_registrations.order_by("created_at"),
            "pages": pages,
        }

        return TemplateResponse(request, "staff/application_detail.html", ctx)

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=self.kwargs["pk"])

        wizard = Wizard(application, form_specs)
        pages = list(wizard.get_pages())

        for page in pages:
            form = page.get_bound_approval_form(request.POST)
            if form.instance.pk:
                form.save()

        return redirect("staff:application-detail", application.pk)


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
