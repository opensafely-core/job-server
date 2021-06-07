from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from ..authorization.decorators import require_superuser
from ..forms import OrgCreateForm
from ..models import Org


@method_decorator(require_superuser, name="dispatch")
class OrgCreate(CreateView):
    form_class = OrgCreateForm
    model = Org
    template_name = "org_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orgs"] = Org.objects.order_by("name")
        return context

    def get_success_url(self):
        return self.object.get_absolute_url()


class OrgDetail(DetailView):
    model = Org
    slug_url_kwarg = "org_slug"
    template_name = "org_detail.html"

    def get_context_data(self, **kwargs):
        projects = self.object.projects.order_by("name")

        context = super().get_context_data(**kwargs)
        context["projects"] = projects
        return context


@method_decorator(require_superuser, name="dispatch")
class OrgList(ListView):
    model = Org
    template_name = "org_list.html"
