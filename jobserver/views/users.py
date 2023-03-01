from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from ..utils import is_safe_path


def login_view(request):
    next_url = request.GET.get("next") or "/"
    if not is_safe_path(next_url):
        next_url = ""

    if request.user.is_authenticated:
        return redirect(next_url)

    return TemplateResponse(request, "login.html", {"next_url": next_url})


@method_decorator(login_required, name="dispatch")
class Settings(UpdateView):
    fields = [
        "fullname",
        "notifications_email",
    ]
    template_name = "settings.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, "Settings saved successfully")

        return response

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return self.request.GET.get("next", "/")
