import inspect

import structlog
from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, UpdateView

from jobserver.authorization import InteractiveReporter, roles
from jobserver.authorization.decorators import require_permission
from jobserver.authorization.utils import roles_for
from jobserver.models import Backend, Job, Org, Project, ProjectMembership, User
from jobserver.utils import raise_if_not_int

from ..forms import UserCreateForm, UserForm, UserOrgsForm
from ..querystring_tools import merge_query_args


logger = structlog.get_logger(__name__)


@method_decorator(require_permission("user_manage"), name="dispatch")
class UserCreate(FormView):
    form_class = UserCreateForm
    template_name = "staff/user_create.html"

    def get_context_data(self, **kwargs):
        query_args = merge_query_args(self.request.GET, {"next": self.request.path}).url

        return super().get_context_data(**kwargs) | {
            "query_args": query_args,
        }

    def get_initial(self):
        initial = {}

        # set the Org if a slug is included in the query args
        if org_slug := self.request.GET.get("org-slug"):
            try:
                initial["org"] = Org.objects.get(slug=org_slug)
            except Org.DoesNotExist:
                pass

        # set the Project if a slug is included in the query args
        if project_slug := self.request.GET.get("project-slug"):
            try:
                initial["project"] = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                pass

        return initial

    @transaction.atomic()
    def form_valid(self, form):
        user = User.objects.create(
            fullname=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            username=form.cleaned_data["email"],
            created_by=self.request.user,
            is_active=True,
        )

        user.orgs.add(form.cleaned_data["org"])

        project = form.cleaned_data["project"]
        if application_url := form.cleaned_data.get("application_url"):
            project.application_url = application_url
            project.save()

        ProjectMembership.objects.create(
            project=project, user=user, roles=[InteractiveReporter]
        )

        # TODO: email user with password [reset] link

        return redirect(user.get_staff_url())


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

        self.object.fullname = form.cleaned_data["fullname"]
        self.object.roles = form.cleaned_data["roles"]
        self.object.save()

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        applications = self.object.applications.order_by("-created_at")
        copiloted_projects = self.object.copiloted_projects.order_by(Lower("name"))
        jobs = Job.objects.filter(job_request__created_by=self.object).order_by(
            "-created_at"
        )[:10]
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
                "name": m.project.title,
                "roles": sorted(r.display_name for r in m.roles),
                "staff_url": m.project.get_staff_url(),
            }
            for m in self.object.project_memberships.order_by(
                "project__number", Lower("project__name")
            )
        ]
        return super().get_context_data(**kwargs) | {
            "applications": applications,
            "copiloted_projects": copiloted_projects,
            "jobs": jobs,
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
            "fullname": self.object.fullname,
        }

    def get_initial(self):
        return super().get_initial() | {
            "backends": self.object.backends.values_list("slug", flat=True),
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
            "missing_names": ["backend", "org", "project"],
            "orgs": Org.objects.order_by("name"),
            "q": self.request.GET.get("q", ""),
            "roles": all_roles,
        }

    def get_queryset(self):
        qs = super().get_queryset()

        # lazily build up some queries for annotation below (Exists uses a
        # subquery, hence the use of OuterRef)
        backends = Backend.objects.filter(members=OuterRef("pk"))
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
            qs = qs.filter(Q(username__icontains=q) | Q(fullname__icontains=q))

        if backend := self.request.GET.get("backend"):
            raise_if_not_int(backend)
            qs = qs.filter(backends__pk=backend)

        if missing := self.request.GET.get("missing"):
            try:
                qs = qs.filter(**{f"{missing}_exists": False})
            except FieldError:
                logger.debug(f"Unknown related object: {missing}")

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
