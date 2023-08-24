from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from jobserver.authorization.decorators import require_manage_backends
from jobserver.models import Backend


@method_decorator(require_manage_backends, name="dispatch")
class BackendCreate(CreateView):
    fields = [
        "name",
        "slug",
        "parent_directory",
        "level_4_url",
        "is_active",
    ]
    model = Backend
    template_name = "staff/backend_create.html"

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_manage_backends, name="dispatch")
class BackendDetail(DetailView):
    model = Backend
    template_name = "staff/backend_detail.html"


@method_decorator(require_manage_backends, name="dispatch")
class BackendEdit(UpdateView):
    fields = [
        "level_4_url",
        "is_active",
    ]
    model = Backend
    template_name = "staff/backend_edit.html"

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_manage_backends, name="dispatch")
class BackendList(ListView):
    def get(self, request, *args, **kwargs):
        context = {"backends": Backend.objects.order_by(Lower("name").asc())}

        return TemplateResponse(request, "staff/backend_list.html", context)


@method_decorator(require_manage_backends, name="dispatch")
class BackendRotateToken(View):
    def post(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, pk=self.kwargs["pk"])

        backend.rotate_token()

        return redirect(backend.get_staff_url())
