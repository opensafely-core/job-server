from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.defaults import bad_request
from django.views.generic import UpdateView

from ..forms import SettingsForm
from ..utils import is_safe_path


def login_view(request):
    next_url = request.GET.get("next", "/")
    if is_safe_path(next_url):
        return TemplateResponse(request, "login.html", {"next_url": next_url})
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
