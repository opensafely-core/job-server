from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, UpdateView, View

from ..authorization.decorators import require_manage_backends
from ..models import Backend


@method_decorator(require_manage_backends, name="dispatch")
class BackendDetail(DetailView):
    model = Backend
    template_name = "backend_detail.html"


@method_decorator(require_manage_backends, name="dispatch")
class BackendEdit(UpdateView):
    fields = ["level_4_url"]
    model = Backend
    template_name = "backend_edit.html"


@method_decorator(require_manage_backends, name="dispatch")
class BackendList(ListView):
    model = Backend
    template_name = "backend_list.html"


@method_decorator(require_manage_backends, name="dispatch")
class BackendRotateToken(View):
    def post(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, pk=self.kwargs["pk"])

        backend.rotate_token()

        return redirect(backend)
