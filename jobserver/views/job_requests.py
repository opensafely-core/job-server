from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.db.models import Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, ListView, RedirectView, View
from pipeline import load_pipeline

from .. import honeycomb
from ..authorization import (
    StaffAreaAdministrator,
    has_permission,
    has_role,
    permissions,
)
from ..backends import backends_to_choices
from ..forms import JobRequestCreateForm
from ..github import _get_github_api
from ..models import Backend, JobRequest, Workspace
from ..pipeline_config import (
    check_cohortextractor_permission,
    check_sqlrunner_permission,
    get_actions,
    get_codelists_status,
    get_database_actions,
    get_project,
    render_definition,
)


class JobRequestCancel(View):
    def post(self, request, *args, **kwargs):
        try:
            job_request = JobRequest.objects.get(pk=self.kwargs["pk"])
        except JobRequest.DoesNotExist:
            raise Http404

        can_cancel_jobs = job_request.created_by == request.user or has_permission(
            request.user, permissions.job_cancel, project=job_request.workspace.project
        )
        if not can_cancel_jobs:
            raise Http404

        if job_request.is_completed:
            return redirect(job_request)

        job_request.request_cancellation()

        messages.success(request, "The requested actions have been cancelled")

        return redirect(job_request)


class JobRequestCreate(CreateView):
    form_class = JobRequestCreateForm
    get_github_api = staticmethod(_get_github_api)
    model = JobRequest
    template_name = "job_request/create.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(
                project__slug=self.kwargs["project_slug"],
                name=self.kwargs["workspace_slug"],
            )
        except Workspace.DoesNotExist:
            return redirect("/")

        if not has_permission(
            request.user, permissions.job_run, project=self.workspace.project
        ):
            raise Http404

        if self.workspace.is_archived:
            msg = (
                "You cannot create Jobs for an archived Workspace."
                "Please contact an admin if you need to have it unarchved."
            )
            messages.error(request, msg)
            return redirect(self.workspace)

        # some backends might need to be disabled.  This view only uses
        # backends the user can see so we look them up here, removing the
        # relevant ones from the QS before we check if there are any below.
        # The form, in get_form_kwargs, will also use the backends constructed
        # here to be consistent.
        self.backends = request.user.backends.all()
        if settings.DISABLE_CREATING_JOBS:
            self.backends = self.backends.exclude(Q(slug="emis") | Q(slug="tpp"))

        # jobs need to be run on a backend so the user needs to have access to
        # at least one
        if not self.backends.exists():
            raise Http404

        # build actions as list or render the exception to the page
        ref = self.kwargs.get("ref", self.workspace.branch)
        try:
            self.project = get_project(
                self.workspace.repo.owner,
                self.workspace.repo.name,
                ref,
            )
            data = load_pipeline(self.project)
            check_cohortextractor_permission(self.workspace.project, data)
            check_sqlrunner_permission(self.workspace.project, data)
            # Find the status of the codelists in this workspace and branch
            # Codelist status is either "ok" or "error"
            self.codelists_status = get_codelists_status(
                self.workspace.repo.owner,
                self.workspace.repo.name,
                ref,
            )
        except Exception as e:
            self.actions = []
            self.database_actions = []
            self.codelists_status = None
            # this is a bit nasty, need to mirror what get/post would set up for us
            self.object = None
            context = self.get_context_data(actions_error=str(e))
            return self.render_to_response(context=context)

        self.actions = list(get_actions(data))

        # Find ehrql/cohort-extractor actions that will use codelists
        self.database_actions = list(get_database_actions(data))
        if self.codelists_status != "ok":
            # At this stage we don't know whether requested jobs depend on
            # codelists, so just show a warning.
            #
            # message.level 9000 is a magic number to trigger the correct alert
            # component to be shown.
            messages.add_message(
                request, 9000, "codelist_out_of_date", "codelist_out_of_date"
            )

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        if (sha := self.kwargs.get("ref")) is None:
            # if a ref wasn't passed in the URL convert the branch to a sha
            sha = self.get_github_api().get_branch_sha(
                self.workspace.repo.owner,
                self.workspace.repo.name,
                self.workspace.branch,
            )

        backend = Backend.objects.get(slug=form.cleaned_data.pop("backend"))
        backend.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            project_definition=self.project,
            codelists_ok=self.codelists_status == "ok",
            **form.cleaned_data,
        )
        return redirect(
            "workspace-logs",
            project_slug=self.workspace.project.slug,
            workspace_slug=self.workspace.name,
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "actions": self.actions,
            "latest_job_request": self.get_latest_job_request(),
            "workspace": self.workspace,
        }

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "actions": [a["name"] for a in self.actions],
            "backends": backends_to_choices(self.backends),
            "database_actions": self.database_actions,
            "codelists_status": self.codelists_status,
        }

    def get_initial(self):
        # derive will_notify for the JobRequestCreateForm from the Workspace
        # setting as a default for the form which the user can override.
        return {"will_notify": self.workspace.should_notify}

    def get_latest_job_request(self):
        return (
            self.workspace.job_requests.with_started_at()
            .order_by("-created_at")
            .first()
        )


class JobRequestDetail(View):
    def get(self, request, *args, **kwargs):
        try:
            job_request = (
                JobRequest.objects.with_started_at()
                .select_related("backend", "created_by", "workspace")
                .prefetch_related("workspace__project__orgs")
                .annotate(
                    last_updated_at=Max("jobs__updated_at", default=timezone.now())
                )
                .get(
                    workspace__project__slug=self.kwargs["project_slug"],
                    workspace__name=self.kwargs["workspace_slug"],
                    pk=self.kwargs["pk"],
                )
            )
        except (JobRequest.DoesNotExist, MultipleObjectsReturned):
            raise Http404

        jobs = job_request.jobs.order_by("started_at")

        # we encode errors raised by job-runner when processing a JobRequest by
        # misusing a Job, since that's our only method of returning messages
        # from job-runner to job-server.  These misused jobs use the __error__
        # action to differentiate themselves.
        is_invalid = jobs.filter(action="__error__").exists()

        can_cancel_jobs = job_request.created_by == request.user or has_permission(
            request.user, permissions.job_cancel, project=job_request.workspace.project
        )
        honeycomb_can_view_links = has_role(self.request.user, StaffAreaAdministrator)

        # build up is_missing_updates to define if we've not seen the backend
        # running this JobRequest for a while.
        # it's completed, we don't expect updates now
        incomplete = not job_request.is_completed

        # was the last update more than our threshold ago?  The last_updated_at
        # annotation uses a default of `now` so we don't have to deal with None
        # here.
        delta = timezone.now() - job_request.last_updated_at
        threshold = timedelta(minutes=30)
        over_30_minutes_ago = delta > threshold

        is_missing_updates = incomplete and over_30_minutes_ago

        previous_jobrequest = JobRequest.objects.previous(job_request)
        code_compare_url = (
            job_request.workspace.repo.get_compare_url(
                previous_jobrequest.sha, job_request.sha
            )
            if previous_jobrequest
            else None
        )

        previous_suceeded_jobrequest = JobRequest.objects.previous(
            job_request, filter_succeeded=True
        )
        code_compare_succeeded_url = (
            job_request.workspace.repo.get_compare_url(
                previous_suceeded_jobrequest.sha, job_request.sha
            )
            if previous_suceeded_jobrequest
            else None
        )

        context = {
            "honeycomb_can_view_links": honeycomb_can_view_links,
            "honeycomb_links": {},
            "is_missing_updates": is_missing_updates,
            "is_invalid": is_invalid,
            "job_request": job_request,
            "jobs": jobs,
            "project_yaml": self.get_project_yaml(job_request),
            "code_compare_url": code_compare_url,
            "code_compare_succeeded_url": code_compare_succeeded_url,
            "user_can_cancel_jobs": can_cancel_jobs,
            "view": self,
        }

        if honeycomb_can_view_links:
            context["honeycomb_links"]["Job Request"] = honeycomb.jobrequest_link(
                job_request
            )

        return TemplateResponse(request, "job_request/detail.html", context=context)

    def get_project_yaml(self, job_request):
        is_empty = job_request.project_definition == ""

        # We know files that are 2.43MB take too long to render with pygments
        # in production and crash browser tabs locally, so we're limiting the
        # size.  The current 1MB is arbitrary until we can get some telemetry
        # from production.
        is_too_large = len(job_request.project_definition) > 10_000  # ~1MB

        if is_empty:
            project_definition = ""
        else:
            project_definition = mark_safe(
                render_definition(
                    job_request.project_definition,
                    job_request.get_file_url,
                )
            )

        return {
            "definition": project_definition,
            "is_empty": is_empty,
            "is_too_large": is_too_large,
            "url": job_request.get_file_url("project.yaml"),
        }


class JobRequestDetailRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        job_request = get_object_or_404(JobRequest, pk=self.kwargs["pk"])
        return job_request.get_absolute_url()


class JobRequestList(ListView):
    paginate_by = 25
    template_name = "job_request/list.html"

    def get_queryset(self):
        return (
            JobRequest.objects.with_started_at()
            .select_related("backend", "created_by", "workspace")
            .prefetch_related("workspace__project__orgs")
            .order_by("-pk")
        )
