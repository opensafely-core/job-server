import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.template.response import TemplateResponse
from django.views.generic import DetailView, FormView, View
from interactive_templates.dates import END_DATE, START_DATE, WEEK_OF_LATEST_EXTRACT
from interactive_templates.schema import Codelist, v2

from jobserver.authorization import has_permission, permissions
from jobserver.models import Backend
from jobserver.opencodelists import _get_opencodelists_api
from jobserver.reports import process_html
from jobserver.utils import build_spa_base_url

from .forms import AnalysisRequestEditForm, AnalysisRequestForm
from .models import AnalysisRequest
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
            week_of_latest_extract=WEEK_OF_LATEST_EXTRACT,
        )

    def dispatch(self, request, *args, **kwargs):
        # The analysis_request_create permission has been removed as part of
        # sunsetting interactive.
        raise PermissionDenied

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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.report and self.object.report.is_published:
            return self.render_to_response(
                context=self.get_context_data(object=self.object)
            )

        # mirror Django's login_required functionality since we can't decorate
        # the function, but we still want to redirect the user to log in such
        # that they can get back to this view
        if not request.user.is_authenticated:
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
            ):
                path = request.get_full_path()
            return redirect_to_login(path, resolved_login_url)

        if not has_permission(
            request.user, permissions.release_file_view, project=self.object.project
        ):
            raise PermissionDenied

        return self.render_to_response(
            context=self.get_context_data(object=self.object)
        )

    def get_context_data(self, **kwargs):
        report = process_html(self.object.report_content)
        return super().get_context_data(**kwargs) | {
            "report": report,
        }


# TODO: this view is specific to AnalysisRequest report edits currently, as we
# render the AnalysisRequest details above the form for context in the
# template. But it may move to jobserver/views/reports.py in future.
class ReportEdit(FormView):
    form_class = AnalysisRequestEditForm
    template_name = "interactive/report_edit.html"

    def dispatch(self, request, *args, **kwargs):
        # keep hold of the AnalysisRequest object so we can easily use it for
        # the success_url
        self.analysis_request = get_object_or_404(
            AnalysisRequest, slug=self.kwargs["slug"]
        )

        if not has_permission(
            request.user,
            permissions.analysis_request_view,
            project=self.analysis_request.project,
        ):
            raise PermissionDenied

        if not self.analysis_request.report:
            raise Http404

        if self.analysis_request.report.is_locked:
            publish_request = self.analysis_request.report.publish_requests.order_by(
                "-created_at"
            ).first()
            return TemplateResponse(
                request,
                "interactive/report_edit_locked.html",
                context={
                    "analysis_request": self.analysis_request,
                    "publish_request": publish_request,
                },
            )

        self.report = self.analysis_request.report

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "analysis_request": self.analysis_request,
        }

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "instance": self.report,
        }

    def get_success_url(self):
        return self.analysis_request.get_absolute_url()
