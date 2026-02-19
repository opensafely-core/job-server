from datetime import timedelta

import sentry_sdk
import structlog
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
from opentelemetry import trace
from pipeline import load_pipeline

from jobserver.rap_api import RapAPIError

from .. import honeycomb
from ..authorization import has_permission
from ..authorization.permissions import Permission
from ..backends import backends_to_choices
from ..forms import JobRequestCreateForm
from ..github import _get_github_api
from ..models import Backend, JobRequest, Workspace
from ..pipeline_config import (
    check_cohortextractor_usage,
    check_sqlrunner_permission,
    get_actions,
    get_codelists_status,
    get_database_actions,
    get_project,
    render_definition,
)


tracer = trace.get_tracer_provider().get_tracer("job_requests")
logger = structlog.get_logger(__name__)


class JobRequestCancel(View):
    """View for requesting JobRequest cancellation via the RAP API.

    This is written as an extensible view so it can be reused in a couple of
    other places in the UI we allow users to cancel all or part of
    JobRequest."""

    def __init__(self, *args, **kwargs):
        self.job_request = None
        super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        job_request = self.get_objects()

        if not self.user_has_permission_to_cancel(request):
            raise Http404

        if self.is_completed():
            return self.redirect()
        actions_to_cancel = self.actions_to_cancel()
        error_msg = (
            "An unexpected error caused the cancellation to fail. If this "
            "persists, please contact technical support"
        )
        try:
            job_request.request_cancellation(actions_to_cancel=actions_to_cancel)
            messages.success(request, self.success_message())
        except RapAPIError as exc:
            # This is probably rare and not much the user can do except retry.
            logger.error(exc, actions_to_cancel=actions_to_cancel)
            sentry_sdk.capture_exception(exc)
            messages.error(request, error_msg)
        except JobRequest.NoActionsToCancel as exc:
            # This indicates a bug in the view or possibly a very rare race
            # condition. Not much the user can do except retry.
            logger.error(exc, actions_to_cancel=actions_to_cancel)
            sentry_sdk.capture_exception(exc)
            messages.error(request, error_msg)
        except JobRequest.NotStartedYet:
            messages.error(
                request,
                "Could not cancel as job information not available. "
                "If this is a recent Job Request, please wait a minute and retry",
            )

        return self.redirect()

    # These functions can be overriden by derived classes to tweak how the view behaves.
    # Effectively private functions but no leading _ for readability.

    def get_objects(self):
        self.job_request = get_object_or_404(JobRequest, pk=self.kwargs["pk"])
        return self.job_request

    def user_has_permission_to_cancel(self, request):
        return self.job_request.created_by == request.user or has_permission(
            request.user,
            Permission.JOB_CANCEL,
            project=self.job_request.workspace.project,
        )

    def is_completed(self):
        return self.job_request.is_completed

    def actions_to_cancel(self):
        return None  # Indicates 'all active'.

    def success_message(self):
        return "The requested actions have been cancelled"

    def redirect(self):
        return redirect(self.job_request)


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
            request.user, Permission.JOB_RUN, project=self.workspace.project
        ):
            raise Http404

        if self.workspace.is_archived:
            msg = "You cannot create new jobs for an archived workspace. Contact an admin if you require the workspace to be unarchived."
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
            check_cohortextractor_usage(data)
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
        job_request = backend.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            project_definition=self.project,
            codelists_ok=self.codelists_status == "ok",
            **form.cleaned_data,
        )

        # Add tracing attributes to the parent span
        tracing_attributes = dict(
            rap_id=job_request.identifier,
            requested_actions=job_request.requested_actions,
        )
        trace.get_current_span().set_attributes(tracing_attributes)
        # Trace the RAP API call
        with tracer.start_as_current_span(
            "create_rap",
            attributes=dict(
                rap_id=job_request.identifier,
                requested_actions=job_request.requested_actions,
            ),
        ):
            # Invoke the RAP API and handle RapAPIErrors.
            job_count = job_request.request_rap_creation()
            if job_count is not None and job_count > 0:
                # Report success. Note we don't display a count of jobs created, even though we have that
                # from the RAP API response, because the jobs have not been created on job server yet, so
                # won't be immediately displayed in the UI
                messages.success(self.request, self.success_message())
            else:
                # No jobs were created by the RAP controller, either an error, or there was nothing to
                # do; we just report the job request status, and status message (if there is one)
                extra = (
                    f" ({job_request.status_message})"
                    if job_request.status_message
                    else ""
                )
                messages.info(
                    self.request,
                    f"No actions scheduled: {job_request.human_readable_status}{extra}",
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

    def success_message(self):
        return "Requested actions have been scheduled to run."


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
            request.user, Permission.JOB_CANCEL, project=job_request.workspace.project
        )
        honeycomb_can_view_links = has_permission(
            self.request.user, Permission.STAFF_AREA_ACCESS
        )

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

        # Is this file too large to render? Files around 2.43MB crash tabs and
        # render slowly. The 10K character limit (~10-40KB) is arbitrary. It
        # could be refined, perhaps with telemetry. Length is an imperfect
        # proxy for render cost, but better than size, which ignores encoding.
        is_too_large = len(job_request.project_definition) > 10_000  # ~10-40KB

        if is_empty:
            # Nothing to render, may as well not call render_definition.
            project_definition = ""
        elif is_too_large:
            # Skip rendering as the template shouldn't display the result.
            # Return a human-readable string in case the template behavior
            # changes and shows project_definition despite is_too_large.
            project_definition = "This file is too large to render."
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
