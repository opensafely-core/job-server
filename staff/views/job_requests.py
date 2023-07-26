import functools

from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.models import JobRequest, Org, Project, Workspace


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class JobRequestDetail(DetailView):
    context_object_name = "job_request"
    model = JobRequest
    template_name = "staff/job_request_detail.html"


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class JobRequestList(ListView):
    model = JobRequest
    ordering = "-created_at"
    paginate_by = 25
    template_name = "staff/job_request_list.html"

    def get_context_data(self, **kwargs):
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

        workspaces = {
            "is_active": "workspace" in self.request.GET,
            "items": list(Workspace.objects.order_by(Lower("name"))),
            "selected": self.request.GET.get("workspace"),
        }

        return super().get_context_data(**kwargs) | {
            "orgs": orgs,
            "projects": projects,
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
                "workspace__project__org__name",
            ]

            # build up Q objects OR'd together.  We need to build them with
            # functools.reduce so we can optionally add the PK filter to the
            # list
            qwargs = functools.reduce(
                Q.__or__, (Q(**{f"{f}__icontains": q}) for f in fields)
            )

            qs = qs.filter(qwargs)

        if orgs := self.request.GET.getlist("orgs"):
            qs = qs.filter(workspace__project__org__slug__in=orgs)

        if project := self.request.GET.get("project"):
            qs = qs.filter(workspace__project__slug=project)

        if workspace := self.request.GET.get("workspace"):
            qs = qs.filter(workspace__name=workspace)

        return qs.distinct()
