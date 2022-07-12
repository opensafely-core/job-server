from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.defaults import bad_request
from django.views.generic import UpdateView

from ..utils import is_safe_path


def login_view(request):
    next_url = request.GET.get("next", "/")
    if not is_safe_path(next_url):
        return bad_request(request, SuspiciousOperation)

    if request.user.is_authenticated:
        return redirect(next_url)

    return TemplateResponse(request, "login.html", {"next_url": next_url})


@method_decorator(login_required, name="dispatch")
class Settings(UpdateView):
    fields = [
        "notifications_email",
    ]
    template_name = "settings.html"
    success_url = "/"

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, "Settings saved successfully")

        return response

    def get_object(self):
        return self.request.user
