from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View

from interactive.models import AnalysisRequest
from interactive.submit import resubmit_analysis
from jobserver.authorization import StaffAreaAdministrator
from jobserver.authorization.decorators import require_role
from jobserver.github import _get_github_api
from jobserver.models import Project, User

from .qwargs_tools import qwargs


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class AnalysisRequestDetail(DetailView):
    context_object_name = "analysis_request"
    model = AnalysisRequest
    template_name = "staff/analysis_request/detail.html"

    def get_context_data(self, **kwargs):
        publish_requests = (
            self.object.report.publish_requests.all() if self.object.report else []
        )

        return super().get_context_data(**kwargs) | {
            "publish_requests": publish_requests,
        }

    def get_queryset(self):
        return super().get_queryset().select_related("created_by", "project")


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class AnalysisRequestResubmit(View):
    get_github_api = staticmethod(_get_github_api)

    def post(self, request, slug, *args, **kwargs):
        analysis_request = AnalysisRequest.objects.get(pk=slug)
        resubmit_analysis(analysis_request, self.get_github_api)
        return redirect(analysis_request.get_staff_url())


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class AnalysisRequestList(ListView):
    context_object_name = "analysis_request"
    model = AnalysisRequest
    ordering = "-created_at"
    paginate_by = 25
    template_name = "staff/analysis_request/list.html"

    def get_context_data(self, **kwargs):
        projects = (
            Project.objects.filter(analysis_requests__isnull=False)
            .distinct()
            .order_by("number", Lower("name"))
        )

        # sort in Python because `User.name` is a property to pick either
        # get_full_name() or username depending on which one has been populated
        users = sorted(
            User.objects.filter(analysis_requests__isnull=False).distinct(),
            key=lambda u: u.name.lower(),
        )
        return super().get_context_data(**kwargs) | {
            "projects": projects,
            "users": users,
        }

    def get_queryset(self):
        qs = super().get_queryset().select_related("created_by").order_by("-created_at")

        if q := self.request.GET.get("q"):
            fields = [
                "created_by__fullname",
                "created_by__username",
                "title",
            ]
            qs = qs.filter(qwargs(fields, q))

        if self.request.GET.get("has_report") == "yes":
            qs = qs.exclude(report=None)
        if self.request.GET.get("has_report") == "no":
            qs = qs.filter(report=None)

        if project := self.request.GET.get("project"):
            qs = qs.filter(project__slug=project)

        if user := self.request.GET.get("user"):
            qs = qs.filter(created_by__username=user)
        return qs.distinct()
