import json

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView

from jobserver.authorization import has_permission
from jobserver.models import Backend, Project
from jobserver.reports import process_html
from jobserver.utils import build_spa_base_url

from .dates import END_DATE, START_DATE
from .forms import AnalysisRequestForm
from .models import AnalysisRequest
from .opencodelists import _get_opencodelists_api


class AnalysisRequestCreate(FormView):
    form_class = AnalysisRequestForm
    get_opencodelists_api = staticmethod(_get_opencodelists_api)
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

        api = self.get_opencodelists_api()
        self.events = api.get_codelists("snomedct")
        self.medications = api.get_codelists("dmd")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
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
            created_by=self.request.user,
            sha="",
            project_definition="",
            force_run_dependencies=True,
            requested_actions=["run_all"],
        )
        analysis_request = AnalysisRequest.objects.create(
            job_request=job_request,
            project=self.project,
            created_by=self.request.user,
            title="get from form",
            start_date=START_DATE,
            end_date=END_DATE,
            codelist_slug="get from form",
            codelist_name="get from form",
        )

        return redirect(analysis_request)

    def get_context_data(self, **kwargs):
        base_path = build_spa_base_url(self.request.path, self.kwargs.get("path", ""))
        return super().get_context_data(**kwargs) | {
            "base_path": base_path,
            "events": self.events,
            "medications": self.medications,
            "project": self.project,
        }

    def get_form_kwargs(self):
        codelists = self.events + self.medications

        if not self.request.method == "POST":
            return {"codelists": codelists}

        # we're posting the form data as JSON so we need to pull that from the
        # request body
        raw = json.loads(self.request.body)

        # translate the incoming data into something the form can validate
        codelist_2 = {}
        if "codelistB" in raw:
            codelist_2 = {
                "codelist_2_label": raw["codelistB"]["label"],
                "codelist_2_slug": raw["codelistB"]["value"],
                "codelist_2_type": raw["codelistB"]["type"],
            }

        data = {
            "codelist_1_label": raw["codelistA"]["label"],
            "codelist_1_slug": raw["codelistA"]["value"],
            "codelist_1_type": raw["codelistA"]["type"],
            **codelist_2,
            "demographics": raw["demographics"],
            "filter_population": raw["filterPopulation"],
            "frequency": raw["frequency"],
            "time_event": raw["timeEvent"],
            "time_scale": raw["timeScale"],
            "time_value": raw["timeValue"],
        }

        return {"codelists": codelists, "data": data}


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

    def get_context_data(self, **kwargs):
        report = process_html(self.object.report_content)

        return super().get_context_data(**kwargs) | {
            "report": report,
        }
