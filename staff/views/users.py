import inspect

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, UpdateView

from jobserver.authorization import roles
from jobserver.authorization.decorators import require_permission
from jobserver.authorization.utils import roles_for
from jobserver.models import Backend, Org, Project, User
from jobserver.utils import raise_if_not_int

from ..forms import UserForm, UserOrgsForm


@method_decorator(require_permission("user_manage"), name="dispatch")
class UserDetail(UpdateView):
    form_class = UserForm
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "staff/user_detail.html"

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

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        applications = self.object.applications.order_by("-created_at")
        copiloted_projects = self.object.copiloted_projects.order_by(Lower("name"))
        orgs = [
            {
                "name": m.org.name,
                "roles": sorted(r.display_name for r in m.roles),
                "staff_url": m.org.get_staff_url(),
            }
            for m in self.object.org_memberships.order_by("org__name")
        ]
        projects = [
            {
                "name": m.project.name,
                "roles": sorted(r.display_name for r in m.roles),
                "staff_url": m.project.get_staff_url(),
            }
            for m in self.object.project_memberships.order_by("project__name")
        ]
        return super().get_context_data(**kwargs) | {
            "applications": applications,
            "copiloted_projects": copiloted_projects,
            "orgs": orgs,
            "projects": projects,
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
    model = User
    template_name = "staff/user_list.html"

    def get_context_data(self, **kwargs):
        all_roles = [name for name, value in inspect.getmembers(roles, inspect.isclass)]

        return super().get_context_data(**kwargs) | {
            "backends": Backend.objects.order_by("slug"),
            "q": self.request.GET.get("q", ""),
            "orgs": Org.objects.order_by("name"),
            "roles": all_roles,
        }

    def get_queryset(self):
        qs = super().get_queryset()

        # lazily build up some queries for annotation below (Exists uses a
        # subquery, hence the use of OuterRef)
        backends = Org.objects.filter(members=OuterRef("pk"))
        orgs = Org.objects.filter(members=OuterRef("pk"))
        projects = Project.objects.filter(members=OuterRef("pk"))

        # annotate the existance of various related objects so we can add
        # badges if they're missing
        qs = qs.annotate(
            backend_exists=Exists(backends),
            org_exists=Exists(orgs),
            project_exists=Exists(projects),
        ).order_by(Lower("username"))

        # filter on the search query
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )

        if backend := self.request.GET.get("backend"):
            raise_if_not_int(backend)
            qs = qs.filter(backends__pk=backend)

        if org := self.request.GET.get("org"):
            qs = qs.filter(orgs__slug=org)

        if role := self.request.GET.get("role"):
            qs = qs.filter_by_role(role)

        return qs


@method_decorator(require_permission("user_manage"), name="dispatch")
class UserSetOrgs(FormView):
    form_class = UserOrgsForm
    template_name = "staff/user_set_orgs.html"

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        # remove the existing memberships so we can create new ones based on
        # the form values
        self.user.org_memberships.all().delete()
        for org in form.cleaned_data["orgs"]:
            org.memberships.create(user=self.user, created_by=self.request.user)

        return redirect(self.user.get_staff_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "user": self.user,
        }

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "available_orgs": Org.objects.order_by("name"),
        }

    def get_initial(self):
        return super().get_initial() | {
            "orgs": self.user.orgs.values_list("pk", flat=True),
        }
