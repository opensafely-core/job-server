import json

from django.core.exceptions import PermissionDenied
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import DetailView, View
from interactive_templates.schema import Codelist, v2

from jobserver.authorization import has_permission
from jobserver.models import Backend, Project, Report
from jobserver.reports import process_html
from jobserver.utils import build_spa_base_url

from .dates import END_DATE, START_DATE
from .forms import AnalysisRequestForm
from .models import AnalysisRequest
from .opencodelists import _get_opencodelists_api
from .submit import submit_analysis


def build_codelist(data, prefix):
    return Codelist(
        label=data.get(f"{prefix}_label", ""),
        slug=data.get(f"{prefix}_slug", ""),
        type=data.get(f"{prefix}_type", ""),
    )


def from_codelist(data, key, sub_key):
    """
    Get subkey values from the given data dict

    Codelist data is submitted as a dict but we need to flatten that
    out to use with our form fields.  This function mirrors what an
    HTML form's POST data would look like if we had submitted it that
    way so we can pass that into the form to be validated.
    """
    try:
        codelist = data[key]
    except KeyError:
        return ""

    try:
        return codelist[sub_key]
    except KeyError:
        return ""


class AnalysisRequestCreate(View):
    get_opencodelists_api = staticmethod(_get_opencodelists_api)

    def build_analysis(self, *, data, project):
        codelist_1 = build_codelist(data, "codelist_1")
        codelist_2 = build_codelist(data, "codelist_2")

        return v2.Analysis(
            codelist_1=codelist_1,
            codelist_2=codelist_2,
            created_by=self.request.user.email,
            demographics=data["demographics"],
            filter_population=data["filter_population"],
            repo=project.interactive_workspace.repo.url,
            time_ever=data["time_ever"],
            time_scale=data["time_scale"],
            time_value=data["time_value"],
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

    def get_form(self, data):
        """
        Translate the incoming JSON data and instantiate our form with it

        We reshape the given data for validation by our form here.  Django
        forms are designed to work with form data but we're validating a JSON
        structure, with sub-keys, etc in it which we need to flatten out for
        the form.
        """

        data = {
            "codelist_1_label": from_codelist(data, "codelistA", "label"),
            "codelist_1_slug": from_codelist(data, "codelistA", "value"),
            "codelist_1_type": from_codelist(data, "codelistA", "type"),
            "codelist_2_label": from_codelist(data, "codelistB", "label"),
            "codelist_2_slug": from_codelist(data, "codelistB", "value"),
            "codelist_2_type": from_codelist(data, "codelistB", "type"),
            "demographics": data.get("demographics", ""),
            "filter_population": data.get("filterPopulation", ""),
            "purpose": data.get("purpose", ""),
            "report_title": data.get("title", ""),
            "time_ever": data.get("timeEver", ""),
            "time_scale": data.get("timeScale", ""),
            "time_value": data.get("timeValue", ""),
            "project": self.project,
        }

        return AnalysisRequestForm(
            codelists=self.events + self.medications,
            data=data,
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form(json.loads(self.request.body))

        if not form.is_valid():
            return self.render_to_response(request, form=form)

        analysis = self.build_analysis(data=form.cleaned_data, project=self.project)
        title = f"{form.cleaned_data['codelist_1_label']} & {form.cleaned_data['codelist_2_label']}"

        analysis_request = submit_analysis(
            analysis=analysis,
            backend=Backend.objects.get(slug="tpp"),
            creator=request.user,
            project=self.project,
            purpose=form.cleaned_data["purpose"],
            report_title=form.cleaned_data["report_title"],
            title=title,
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
        update_url = reverse(
            "interactive:report-update",
            kwargs=dict(
                slug=self.object.slug,
                project_slug=self.object.project.slug,
                org_slug=self.object.project.org.slug,
            ),
        )

        return super().get_context_data(**kwargs) | {
            "report": report,
            "update_url": update_url,
        }


class AnalysisReportUpdate(View):
    """Updating the title and description of the generated report.

    It actually updates the attached Report model, rather than the
    AnalysisRequest itself.
    """

    form_class = modelform_factory(Report, fields=["title", "description"])

    def dispatch(self, request, slug, *args, **kwargs):
        analysis_request = get_object_or_404(AnalysisRequest, slug=slug)

        if not has_permission(
            self.request.user, "analysis_request_view", project=analysis_request.project
        ):
            raise PermissionDenied

        if not analysis_request.report:
            raise Http404

        self.analysis_request = analysis_request

        return super().dispatch(request, slug, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=self.analysis_request.report)
        return self.render_to_response(request, form)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=self.analysis_request.report)
        if form.is_valid():
            form.save()
            project = self.analysis_request.project
            return redirect(
                "interactive:analysis-detail",
                org_slug=project.org.slug,
                project_slug=project.slug,
                slug=self.analysis_request.slug,
            )
        else:
            return self.render_to_response(request, form)

    def render_to_response(self, request, form):
        return TemplateResponse(
            request,
            template="interactive/report_update.html",
            context={"form": form, "analysis_request": self.analysis_request},
        )
