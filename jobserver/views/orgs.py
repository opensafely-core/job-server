from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from ..authorization.decorators import require_permission
from ..forms import OrgCreateForm
from ..models import Org, Workspace


@method_decorator(require_permission("create_org"), name="dispatch")
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
    template_name = "org_detail.html"

    def get(self, request, *args, **kwargs):
        slug = self.kwargs["org_slug"]

        try:
            org = Org.objects.get(slug=slug)
        except Org.DoesNotExist:
            # we used to serve up Workspaces at the root URL but have moved
            # them under their relevant Orgs & Projects.  So attempt to
            # redirect requests to a valid Workspace here for a while.

            try:
                workspace = Workspace.objects.get(name=slug)
            except Workspace.DoesNotExist:
                raise Http404

            return redirect(workspace)

        is_member = request.user in org.members.all()
        projects = org.projects.order_by("name")

        return TemplateResponse(
            request,
            "org_detail.html",
            context={
                "is_member": is_member,
                "org": org,
                "projects": projects,
            },
        )


class OrgList(ListView):
    queryset = Org.objects.order_by("name")
    template_name = "org_list.html"
