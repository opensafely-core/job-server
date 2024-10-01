from django.contrib import messages
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from jobserver.authorization import StaffAreaAdministrator
from jobserver.authorization.decorators import require_role
from jobserver.models import Backend, JobRequest, Org, Project, User, Workspace

from .qwargs_tools import qwargs


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class JobRequestCancel(View):
    def post(self, request, *args, **kwargs):
        try:
            job_request = JobRequest.objects.get(pk=self.kwargs["pk"])
        except JobRequest.DoesNotExist:
            raise Http404

        if job_request.is_completed:
            return redirect(job_request.get_staff_url())

        job_request.request_cancellation()

        messages.success(request, "The requested actions have been cancelled")

        return redirect(job_request.get_staff_url())


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class JobRequestDetail(DetailView):
    context_object_name = "job_request"
    model = JobRequest
    template_name = "staff/job_request/detail.html"


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class JobRequestList(ListView):
    ordering = "-created_at"
    paginate_by = 25
    template_name = "staff/job_request/list.html"
    queryset = JobRequest.objects.prefetch_related("workspace", "workspace__project")

    def get_context_data(self, **kwargs):
        backends = {
            "is_active": "backends" in self.request.GET,
            "items": list(Backend.objects.order_by(Lower("name"))),
            "selected": self.request.GET.getlist("backends", default=[]),
        }

        orgs = {
            "is_active": "orgs" in self.request.GET,
            "items": list(Org.objects.order_by(Lower("name"))),
            "selected": self.request.GET.getlist("orgs", default=[]),
        }

        projects = {
            "is_active": "project" in self.request.GET,
            "items": list(Project.objects.order_by("number", Lower("name"))),
            "selected": self.request.GET.get("project"),
        }

        users = {
            "is_active": "user" in self.request.GET,
            "items": list(User.objects.order_by(Lower("fullname"), "username")),
            "selected": self.request.GET.get("user"),
        }

        workspaces = {
            "is_active": "workspace" in self.request.GET,
            "items": list(Workspace.objects.order_by(Lower("name"))),
            "selected": self.request.GET.get("workspace"),
        }

        return super().get_context_data(**kwargs) | {
            "backends": backends,
            "orgs": orgs,
            "projects": projects,
            "users": users,
            "workspaces": workspaces,
        }

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("created_by")
            .defer("project_definition")
        )

        if q := self.request.GET.get("q"):
            fields = [
                "created_by__fullname",
                "created_by__username",
                "identifier",
                "jobs__identifier",
                "pk",
                "workspace__name",
                "workspace__project__name",
                "workspace__project__orgs__name",
            ]
            qs = qs.filter(qwargs(fields, q))

        if backends := self.request.GET.getlist("backends"):
            qs = qs.filter(backend__slug__in=backends)

        if orgs := self.request.GET.getlist("orgs"):
            qs = qs.filter(workspace__project__orgs__slug__in=orgs)

        if project := self.request.GET.get("project"):
            qs = qs.filter(workspace__project__slug=project)

        if user := self.request.GET.get("user"):
            qs = qs.filter(created_by__username=user)

        if workspace := self.request.GET.get("workspace"):
            qs = qs.filter(workspace__name=workspace)

        return qs.distinct()
