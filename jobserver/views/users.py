import inspect

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView

from ..authorization import roles
from ..authorization.decorators import require_permission
from ..forms import SettingsForm, UserForm
from ..models import Backend, User


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
class UserDetail(UpdateView):
    form_class = UserForm
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "user_detail.html"

    @transaction.atomic()
    def form_valid(self, form):
        # remove the existing memberships so we can create new ones based on
        # the form values
        self.object.backend_memberships.all().delete()
        for backend in form.cleaned_data["backends"]:
            backend.memberships.create(user=self.object, created_by=self.request.user)

        self.object.roles = form.cleaned_data["roles"]
        self.object.save()

        return redirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "orgs": self.object.orgs.order_by("name"),
            "projects": self.object.projects.order_by("name"),
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # UserForm isn't a ModelForm so don't pass instance to it
        del kwargs["instance"]

        available_roles = [
            value for name, value in inspect.getmembers(roles, inspect.isclass)
        ]

        return kwargs | {
            "available_backends": Backend.objects.order_by("name"),
            "available_roles": available_roles,
        }

    def get_initial(self):
        return super().get_initial() | {
            "backends": self.object.backends.values_list("name", flat=True),
            "roles": self.object.roles,
        }


@method_decorator(require_permission("manage_users"), name="dispatch")
class UserList(ListView):
    queryset = User.objects.order_by("username")
    template_name = "user_list.html"
