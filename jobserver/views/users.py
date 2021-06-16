from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView

from ..authorization.decorators import require_permission
from ..forms import SettingsForm
from ..models import User


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


@method_decorator(require_permission("manage_users"), name="dispatch")
class UserList(ListView):
    queryset = User.objects.order_by("username")
    template_name = "user_list.html"
