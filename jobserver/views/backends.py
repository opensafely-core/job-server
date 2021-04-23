from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from ..authorization.decorators import require_superuser
from ..models import Backend


@method_decorator(require_superuser, name="dispatch")
class BackendDetail(DetailView):
    model = Backend
    template_name = "backend_detail.html"


@method_decorator(require_superuser, name="dispatch")
class BackendList(ListView):
    model = Backend
    template_name = "backend_list.html"


@method_decorator(require_superuser, name="dispatch")
class BackendRotateToken(View):
    def post(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, pk=self.kwargs["pk"])

        backend.rotate_token()

        return redirect(backend)
