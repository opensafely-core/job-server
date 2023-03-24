import json

from attrs import asdict
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import DetailView, View
from interactive_templates.schema import Codelist, v2

from jobserver.authorization import has_permission
from jobserver.models import Backend, Project
from jobserver.reports import process_html
from jobserver.utils import build_spa_base_url

from .dates import END_DATE, START_DATE
from .forms import AnalysisRequestForm
from .models import AnalysisRequest
from .opencodelists import _get_opencodelists_api
from .submit import submit_analysis


def build_codelist(data):
    if data is None:
        return

    return Codelist(
        label=data.get("label", ""),
        slug=data.get("value", ""),
        type=data.get("type", ""),
    )


class AnalysisRequestCreate(View):
    form_class = AnalysisRequestForm
    get_opencodelists_api = staticmethod(_get_opencodelists_api)

    def build_analysis(self, *, form_data, project):
        raw = json.loads(form_data)

        return v2.Analysis(
            codelist_1=build_codelist(raw.get("codelistA", None)),
            codelist_2=build_codelist(raw.get("codelistB", None)),
            created_by=self.request.user.email,
            demographics=raw.get("demographics", []),
            filter_population=raw.get("filterPopulation", ""),
            purpose=raw.get("purpose", ""),
            repo=project.interactive_workspace.repo.url,
            time_scale=raw.get("timeScale", ""),
            time_value=int(raw.get("timeValue", 0)),
            title=raw.get("title", ""),
            start_date=START_DATE,
            end_date=END_DATE,
        )

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

        self.codelists_api = self.get_opencodelists_api()
        self.events = self.codelists_api.get_codelists("snomedct")
        self.medications = self.codelists_api.get_codelists("dmd")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(request)

    def post(self, request, *args, **kwargs):
        # we're posting the form data as JSON so we need to pull that from the
        # request body
        analysis = self.build_analysis(
            form_data=self.request.body, project=self.project
        )

        form = AnalysisRequestForm(
            codelists=self.events + self.medications,
            data=self.translate_for_form(asdict(analysis)),
        )

        if not form.is_valid():
            return self.render_to_response(request, form=form)

        analysis_request = submit_analysis(
            analysis=analysis,
            backend=Backend.objects.get(slug="tpp"),
            creator=request.user,
            project=self.project,
        )

        return redirect(analysis_request)

    def render_to_response(self, request, **context):
        """
        Render a response with the given request and context

        This is a cut-down version of Django's render_to_response and
        get_context_data methods.  We aren't using our form instace to
        generate errors for the UI so we don't need to handle construction
        of it in both GET/POST so all our context construction can also
        happen here.
        """
        base_path = build_spa_base_url(self.request.path, self.kwargs.get("path", ""))

        context = context | {
            "base_path": base_path,
            "events": self.events,
            "medications": self.medications,
            "project": self.project,
            "start_date": START_DATE,
            "end_date": END_DATE,
        }

        return TemplateResponse(
            request,
            template="interactive/analysis_request_create.html",
            context=context,
        )

    def translate_for_form(self, data):
        """
        Reshape the given data for validation by a Django Form

        Django forms are designed to work with form data but we're validating
        a JSON structure, with sub-keys, etc in it which we need to flatten out
        for the form.
        """

        def flatten(key, data):
            old = data.pop(key)
            if old is None:
                return data

            new = {f"{key}_{k}": v for k, v in old.items()}

            return data | new

        data = flatten("codelist_1", data)
        data = flatten("codelist_2", data)

        return data


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
