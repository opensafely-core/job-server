from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, TemplateView

from jobserver.authorization import has_permission
from jobserver.models import Backend, Project

from .dates import END_DATE, START_DATE
from .models import AnalysisRequest


class AnalysisRequestCreate(TemplateView):
    template_name = "interactive/analysis_request_create.html"

    def dispatch(self, request, *args, **kwargs):
        # even though an AnalysisRequest is a superset of a JobRequest, an
        # object that lives below a Workspace, we hide workspaces from the
        # interactive view, treating them as an implementation detail for this
        # method of using the service.  As such users see the interactive
        # pages in the context of a project, including the URL.
        self.project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        if not has_permission(
            request.user, "analysis_request_create", project=self.project
        ):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "project": self.project,
        }

    def post(self, request, *args, **kwargs):
        # OSI v1 does the following:
        # * copy the report template over, interpolating details into project.yaml
        # * commit to repo
        # * create a job request
        # * create an issue
        # * send confirmation email

        # create some required objects so we can create skeleton views as we
        # build up the functionality of interactive
        job_request = self.project.interactive_workspace.job_requests.create(
            backend=Backend.objects.get(slug="tpp"),
            created_by=request.user,
            sha="",
            project_definition="",
            force_run_dependencies=True,
            requested_actions=["run_all"],
        )
        analysis_request = AnalysisRequest.objects.create(
            job_request=job_request,
            project=self.project,
            created_by=request.user,
            title="get from form",
            start_date=START_DATE,
            end_date=END_DATE,
            codelist_slug="get from form",
            codelist_name="get from form",
        )

        return redirect(analysis_request)


class AnalysisRequestDetail(DetailView):
    context_object_name = "analysis_request"
    model = AnalysisRequest
    template_name = "interactive/analysis_request_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)

        if not has_permission(
            self.request.user, "analysis_request_view", project=obj.project
        ):
            raise PermissionDenied

        return obj
