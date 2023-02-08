import json

from attrs import asdict
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import DetailView, View

from jobserver.authorization import has_permission
from jobserver.models import Backend, Project
from jobserver.reports import process_html
from jobserver.utils import build_spa_base_url

from . import Analysis, Codelist
from .forms import AnalysisRequestForm
from .models import AnalysisRequest
from .opencodelists import _get_opencodelists_api
from .submit import submit_analysis


def get(d, path, default=""):
    """Return the value at a given path or the default"""
    key, _, remainder = path.partition(".")

    value = d.get(key, default)

    if not isinstance(value, dict):
        return value
    else:
        return get(value, remainder, default)


class AnalysisRequestCreate(View):
    form_class = AnalysisRequestForm
    get_opencodelists_api = staticmethod(_get_opencodelists_api)

    def build_analysis(self, *, form_data, project):
        raw = json.loads(form_data)

        # translate the incoming data into something the form can validate
        codelist_2 = None
        if "codelistB" in raw:
            codelist_2 = Codelist(
                **{
                    "label": get(raw, "codelistB.label"),
                    "slug": get(raw, "codelistB.value"),
                    "type": get(raw, "codelistB.type"),
                }
            )

        # add auth token if it's a real github repo
        # TODO: needs a new token for this
        repo = project.interactive_workspace.repo.url
        if repo.startswith("https://github.com"):
            repo = repo.replace(
                "https://", f"https://interactive:{settings.GITHUB_WRITEABLE_TOKEN}@"
            )  # pragma: no cover

        return Analysis(
            codelist_1=Codelist(
                **{
                    "label": get(raw, "codelistA.label"),
                    "slug": get(raw, "codelistA.value"),
                    "type": get(raw, "codelistA.type"),
                }
            ),
            codelist_2=codelist_2,
            created_by=self.request.user.email,
            demographics=get(raw, "demographics"),
            filter_population=get(raw, "filterPopulation"),
            frequency=get(raw, "frequency"),
            repo=repo,
            time_event=get(raw, "timeEvent"),
            time_scale=get(raw, "timeScale"),
            time_value=get(raw, "timeValue"),
            title=get(raw, "title"),
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
            get_opencodelists_api=self.get_opencodelists_api,
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
