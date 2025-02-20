import structlog
from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, Sum
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from social_django.models import UserSocialAuth

from jobserver.auditing.presenters.lookup import get_presenter
from jobserver.authorization import permissions
from jobserver.authorization.decorators import require_permission
from jobserver.authorization.forms import RolesForm
from jobserver.authorization.global_roles import GLOBAL_ROLE_NAMES
from jobserver.authorization.utils import roles_for, strings_to_roles
from jobserver.commands import users
from jobserver.models import (
    AuditableEvent,
    Backend,
    Job,
    Org,
    Project,
    User,
)
from jobserver.utils import raise_if_not_int

from ..forms import UserForm, UserOrgsForm
from ..querystring_tools import get_next_url
from .qwargs_tools import qwargs


logger = structlog.get_logger(__name__)


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserAuditLog(ListView):
    paginate_by = 25
    template_name = "staff/user/audit_log.html"

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        events = self.get_queryset()
        presentable_events = [get_presenter(e)(event=e) for e in events]

        types = AuditableEvent.get_types(prefix="project_member")

        # Note: we're passing in presentable_events here to override the use of
        # self.object_list which is an iterable of AuditableEvents, but we're
        # going to be using presentable_events in the template so we want to
        # paginate on those instead.
        return super().get_context_data(object_list=presentable_events, **kwargs) | {
            "events": presentable_events,
            "user": self.user,
            "types": types,
        }

    def get_queryset(self):
        project_pks = [
            str(pk) for pk in self.user.projects.values_list("pk", flat=True)
        ]
        is_member = Q(
            target_model=Project._meta.label,
            target_id__in=project_pks,
        )

        qs = AuditableEvent.objects.filter(
            Q(created_by=self.user.username)
            | Q(target_user=self.user.username)
            | is_member
        ).order_by("-created_at", "-pk")

        if types := self.request.GET.getlist("types"):
            qs = qs.filter(type__in=types)

        return qs.distinct()


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserClearRoles(View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=self.kwargs["username"])

        users.clear_all_roles(user=user, by=request.user)

        return redirect(get_next_url(request.GET, user.get_staff_roles_url()))


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserDetail(SingleObjectMixin, View):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def dispatch(self, request, *args, **kwargs):
        user = self.get_object()

        view = UserDetailWithOAuth if user.uses_social_auth else UserDetailWithEmail
        return view.as_view()(request, *args, **kwargs)


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserDetailWithEmail(UpdateView):
    fields = [
        "fullname",
        "email",
    ]
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "staff/user/detail_with_email.html"

    def get_context_data(self, **kwargs):
        orgs = [
            {
                "name": m.org.name,
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
            "orgs": orgs,
            "projects": projects,
        }

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserDetailWithOAuth(UpdateView):
    form_class = UserForm
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "staff/user/detail_with_oauth.html"

    @transaction.atomic()
    def form_valid(self, form):
        # remove the existing memberships so we can create new ones based on
        # the form values
        self.object.backend_memberships.all().delete()
        for backend in form.cleaned_data["backends"]:
            backend.memberships.create(user=self.object, created_by=self.request.user)

        self.object.fullname = form.cleaned_data["fullname"]
        self.object.save()

        return redirect(self.object.get_staff_url())

    def get_context_data(self, **kwargs):
        applications = self.object.applications.order_by("-created_at")
        copiloted_projects = self.object.copiloted_projects.order_by(Lower("name"))
        jobs = Job.objects.filter(job_request__created_by=self.object).order_by(
            "-created_at"
        )
        orgs = self.object.orgs.order_by(Lower("name"))
        projects = self.object.projects.order_by("number", Lower("name"))

        return super().get_context_data(**kwargs) | {
            "applications": applications,
            "copiloted_projects": copiloted_projects,
            "jobs": jobs[:10],
            "job_count": jobs.count(),
            "orgs": orgs,
            "projects": projects,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # UserForm isn't a ModelForm so don't pass instance to it
        del kwargs["instance"]

        return kwargs | {
            "available_backends": Backend.objects.order_by("slug"),
            "fullname": self.object.fullname,
        }

    def get_initial(self):
        return super().get_initial() | {
            "backends": self.object.backends.values_list("slug", flat=True),
        }


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserList(ListView):
    model = User
    paginate_by = 25
    template_name = "staff/user/list.html"
    queryset = User.objects.all().prefetch_related(
        "project_memberships", "org_memberships"
    )

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "backends": Backend.objects.order_by("slug"),
            "missing_names": ["backend", "org", "project"],
            "orgs": Org.objects.order_by("name"),
            "q": self.request.GET.get("q", ""),
            "roles": GLOBAL_ROLE_NAMES,
        }

    def get_queryset(self):
        qs = super().get_queryset()

        # lazily build up some queries for annotation below (Exists uses a
        # subquery, hence the use of OuterRef)
        backends = Backend.objects.filter(members=OuterRef("pk"))
        orgs = Org.objects.filter(members=OuterRef("pk"))
        projects = Project.objects.filter(members=OuterRef("pk"))
        social_auths = UserSocialAuth.objects.filter(user__pk=OuterRef("pk"))

        # annotate the existance of various related objects so we can add
        # badges if they're missing
        qs = qs.annotate(
            backend_exists=Exists(backends),
            is_github_user=Exists(social_auths),
            org_exists=Exists(orgs),
            project_exists=Exists(projects),
        ).order_by(*self.model._meta.ordering)

        # filter on the search query
        if q := self.request.GET.get("q"):
            fields = [
                "fullname",
                "username",
            ]
            qs = qs.filter(qwargs(fields, q))

        if backend := self.request.GET.get("backend"):
            raise_if_not_int(backend)
            qs = qs.filter(backends__pk=backend)

        if missing := self.request.GET.get("missing"):
            try:
                qs = qs.filter(is_github_user=True, **{f"{missing}_exists": False})
            except FieldError:
                logger.debug(f"Unknown related object: {missing}")

        if org := self.request.GET.get("org"):
            qs = qs.filter(orgs__slug=org)

        if role := self.request.GET.get("role"):
            roles = strings_to_roles([role])
            qs = qs.filter(roles__contains=roles)

        if any_roles := self.request.GET.get("any_roles"):
            # build up a query that checks for any roles or no roles.  We have
            # to check for the presence of the *_memberships relations as well
            # as traversing to their roles fields
            qs = qs.annotate(
                project_roles_count=Sum("project_memberships__roles__len"),
            )
            project_roles = Q(project_memberships=None) | Q(project_roles_count=0)
            query = Q(roles=[]) & project_roles

            if any_roles == "yes":
                qs = qs.exclude(query)
            elif any_roles == "no":
                qs = qs.filter(query)

        return qs.distinct()


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserRoleList(FormView):
    form_class = RolesForm
    template_name = "staff/user/role_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.user.roles = form.cleaned_data["roles"]
        self.user.save(update_fields=["roles"])

        return redirect(self.user.get_staff_roles_url())

    def get_context_data(self, **kwargs):
        project_memberships_with_roles = self.user.project_memberships.exclude(
            roles=[]
        ).order_by("project__number", Lower("project__name"))

        return super().get_context_data(**kwargs) | {
            "projects": project_memberships_with_roles,
            "user": self.user,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        return kwargs | {"available_roles": roles_for(User)}

    def get_initial(self):
        return super().get_initial() | {"roles": self.user.roles}


@method_decorator(require_permission(permissions.user_manage), name="dispatch")
class UserSetOrgs(FormView):
    form_class = UserOrgsForm
    template_name = "staff/user/set_orgs.html"

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
