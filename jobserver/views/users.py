from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.defaults import bad_request
from django.views.generic import TemplateView, UpdateView

from ..forms import SettingsForm
from ..utils import is_safe_path


class Login(TemplateView):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        if is_safe_path(request.GET.get("next", "")):
            return render(request, self.template_name)
        else:
            return bad_request(request, SuspiciousOperation)


@method_decorator(login_required, name="dispatch")
class Settings(UpdateView):
    form_class = SettingsForm
    template_name = "settings.html"
    success_url = "/"

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, "Settings saved successfully")

        return response

    def get_object(self):
        return self.request.user
