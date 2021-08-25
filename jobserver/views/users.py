import inspect

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView

from ..authorization import roles
from ..authorization.decorators import require_permission
from ..authorization.utils import roles_for
from ..forms import SettingsForm, UserForm
from ..models import Backend, User
from ..utils import raise_if_not_int


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


@method_decorator(require_permission("user_manage"), name="dispatch")
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

        self.object.is_superuser = form.cleaned_data["is_superuser"]
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

        available_roles = roles_for(User)

        return kwargs | {
            "available_backends": Backend.objects.order_by("slug"),
            "available_roles": available_roles,
        }

    def get_initial(self):
        return super().get_initial() | {
            "backends": self.object.backends.values_list("slug", flat=True),
            "is_superuser": self.object.is_superuser,
            "roles": self.object.roles,
        }


@method_decorator(require_permission("user_manage"), name="dispatch")
class UserList(ListView):
    queryset = User.objects.order_by(Lower("username"))
    template_name = "user_list.html"

    def get_context_data(self, **kwargs):
        all_roles = [name for name, value in inspect.getmembers(roles, inspect.isclass)]

        return super().get_context_data(**kwargs) | {
            "backends": Backend.objects.order_by("slug"),
            "q": self.request.GET.get("q", ""),
            "roles": all_roles,
        }

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )

        backend = self.request.GET.get("backend")
        if backend:
            raise_if_not_int(backend)
            qs = qs.filter(backends__pk=backend)

        role = self.request.GET.get("role")
        if role:
            qs = qs.filter_by_role(role)

        return qs
