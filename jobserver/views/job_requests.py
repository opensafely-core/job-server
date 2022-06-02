import functools
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, ListView, RedirectView, View
from django.views.generic.edit import FormMixin
from first import first
from opentelemetry import trace
from pipeline import load_pipeline

from ..authorization import CoreDeveloper, has_permission, has_role
from ..backends import backends_to_choices
from ..forms import JobRequestCreateForm, JobRequestSearchForm
from ..github import get_branch_sha, get_commits
from ..models import Backend, JobRequest, User, Workspace
from ..pipeline_config import get_actions, get_project, render_definition
from ..utils import raise_if_not_int


tracer = trace.get_tracer(__name__)


def filter_by_status(job_requests, status):
    """
    Filter JobRequests by status property

    JobRequest.status is built by "bubbling up" the status of each related Job.
    However, the construction of that property isn't easily converted to a
    QuerySet, hence this function.
    """
    with tracer.start_as_current_span("filter_by_status"):
        if status not in ["failed", "running", "pending", "succeeded"]:
            # status is taken from a GET query arg so we need to treat it as user
            # input, returning the full JobRequest QuerySet if it's not a valid
            # value.
            return job_requests

        return [r for r in job_requests.all() if r.status.lower() == status]


class JobRequestCancel(View):
    def post(self, request, *args, **kwargs):
        try:
            job_request = JobRequest.objects.get(pk=self.kwargs["pk"])
        except JobRequest.DoesNotExist:
            raise Http404

        can_cancel_jobs = job_request.created_by == request.user or has_permission(
            request.user, "job_cancel", project=job_request.workspace.project
        )
        if not can_cancel_jobs:
            raise Http404

        if job_request.is_completed:
            return redirect(job_request)

        # Exclude succeeded jobs (failed or succeeded status, consistent with Job.is_completed method)
        actions = list(
            set(
                job_request.jobs.exclude(
                    status__in=["failed", "succeeded"]
                ).values_list("action", flat=True)
            )
        )

        job_request.cancelled_actions = actions
        job_request.save()

        return redirect(job_request)


class JobRequestCreate(CreateView):
    form_class = JobRequestCreateForm
    model = JobRequest
    template_name = "job_request_create.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.workspace = Workspace.objects.get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                name=self.kwargs["workspace_slug"],
            )
        except Workspace.DoesNotExist:
            return redirect("/")

        if not has_permission(request.user, "job_run", project=self.workspace.project):
            raise Http404

        if self.workspace.is_archived:
            msg = (
                "You cannot create Jobs for an archived Workspace."
                "Please contact an admin if you need to have it unarchved."
            )
            messages.error(request, msg)
            return redirect(self.workspace)

        # jobs need to be run on a backend so the user needs to have access to
        # at least one
        if not request.user.backends.exists():
            raise Http404

        # build actions as list or render the exception to the page
        ref = self.kwargs.get("ref", self.workspace.branch)
        try:
            self.project = get_project(
                self.workspace.repo_owner,
                self.workspace.repo_name,
                ref,
            )
            data = load_pipeline(self.project)
        except Exception as e:
            self.actions = []
            # this is a bit nasty, need to mirror what get/post would set up for us
            self.object = None
            context = self.get_context_data(actions_error=str(e))
            return self.render_to_response(context=context)

        self.actions = list(get_actions(data))
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        if (sha := self.kwargs.get("ref")) is None:
            # if a ref wasn't passed in the URL convert the branch to a sha
            sha = get_branch_sha(
                self.workspace.repo_owner,
                self.workspace.repo_name,
                self.workspace.branch,
            )

        backend = Backend.objects.get(slug=form.cleaned_data.pop("backend"))
        backend.job_requests.create(
            workspace=self.workspace,
            created_by=self.request.user,
            sha=sha,
            project_definition=self.project,
            **form.cleaned_data,
        )
        return redirect(
            "workspace-logs",
            org_slug=self.workspace.project.org.slug,
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
        kwargs = super().get_form_kwargs()
        kwargs["actions"] = [a["name"] for a in self.actions]

        # get backends from the current user
        backends = Backend.objects.filter(
            memberships__in=self.request.user.backend_memberships.all()
        )
        kwargs["backends"] = backends_to_choices(backends)

        return kwargs

    def get_initial(self):
        # derive will_notify for the JobRequestCreateForm from the Workspace
        # setting as a default for the form which the user can override.
        return {"will_notify": self.workspace.should_notify}

    def get_latest_job_request(self):
        return self.workspace.job_requests.order_by("-created_at").first()


class JobRequestDetail(View):
    def get(self, request, *args, **kwargs):
        try:
            job_request = JobRequest.objects.select_related(
                "created_by", "workspace"
            ).get(
                workspace__project__org__slug=self.kwargs["org_slug"],
                workspace__project__slug=self.kwargs["project_slug"],
                workspace__name=self.kwargs["workspace_slug"],
                pk=self.kwargs["pk"],
            )
        except (JobRequest.DoesNotExist, MultipleObjectsReturned):
            raise Http404

        can_cancel_jobs = job_request.created_by == request.user or has_permission(
            request.user, "job_cancel", project=job_request.workspace.project
        )

        project_definition = mark_safe(
            render_definition(
                job_request.project_definition,
                job_request.get_file_url,
            )
        )

        honeycomb_context_starttime = job_request.created_at - timedelta(days=2)

        honeycomb_context_endtime = None
        if job_request.completed_at is not None:
            honeycomb_context_endtime = job_request.completed_at + timedelta(days=2)

        context = {
            "honeycomb_context_starttime": honeycomb_context_starttime,
            "honeycomb_context_endtime": honeycomb_context_endtime,
            "job_request": job_request,
            "project_definition": project_definition,
            "project_yaml_url": job_request.get_file_url("project.yaml"),
            "user_can_cancel_jobs": can_cancel_jobs,
            "user_can_cancel_jobs": can_cancel_jobs,
            "view": self,
        }
        return TemplateResponse(request, "job_request_detail.html", context=context)


class JobRequestDetailRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        job_request = get_object_or_404(JobRequest, pk=self.kwargs["pk"])
        return job_request.get_absolute_url()


class JobRequestList(FormMixin, ListView):
    form_class = JobRequestSearchForm
    paginate_by = 25
    template_name = "job_request_list.html"

    def get_context_data(self, **kwargs):
        with tracer.start_as_current_span("get_context_data"):
            # only get Users created via GitHub OAuth
            users = User.objects.exclude(social_auth=None)
            users = sorted(users, key=lambda u: u.name.lower())

            workspaces = Workspace.objects.filter(is_archived=False).order_by("name")

            # filter object list based on status arg
            filtered_object_list = filter_by_status(
                self.object_list, self.request.GET.get("status")
            )
            context = super().get_context_data(
                object_list=filtered_object_list, **kwargs
            )

            context["backends"] = Backend.objects.order_by("slug")
            context["is_core_dev"] = has_role(self.request.user, CoreDeveloper)
            context["statuses"] = ["failed", "running", "pending", "succeeded"]
            context["users"] = {u.username: u.name for u in users}
            context["workspaces"] = workspaces
            return context

    def get_queryset(self):
        with tracer.start_as_current_span("get_queryset"):
            qs = JobRequest.objects.select_related("backend", "workspace").order_by(
                "-pk"
            )

            q = self.request.GET.get("q")
            if q:
                qwargs = Q(jobs__action__icontains=q) | Q(jobs__identifier__icontains=q)
                try:
                    q = int(q)
                except ValueError:
                    qs = qs.filter(qwargs)
                else:
                    # if the query looks enough like a number for int() to handle
                    # it then we can look for a job number
                    qs = qs.filter(qwargs | Q(jobs__pk=q))

            backend = self.request.GET.get("backend")
            if backend:
                raise_if_not_int(backend)
                qs = qs.filter(backend_id=backend)

            username = self.request.GET.get("username")
            if username:
                qs = qs.filter(created_by__username=username)

            workspace = self.request.GET.get("workspace")
            if workspace:
                raise_if_not_int(workspace)
                qs = qs.filter(workspace_id=workspace)

            return qs

    def form_valid(self, form):
        identifier = form.cleaned_data["identifier"]

        job_request = JobRequest.objects.filter(
            identifier__icontains=identifier
        ).first()

        if not job_request:
            msg = f"Could not find a JobRequest with the identfier '{identifier}'"
            form.add_error("identifier", msg)
            return self.form_invalid(form)

        return redirect(job_request)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed POST
        variables and then check if it's valid.

        Form validity dispatch copied from Django's CBVs, modified so to
        generate object_list for when form_invalid() is called.
        """
        self.object_list = self.get_queryset()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class JobRequestPickRef(View):
    def get(self, request, *args, **kwargs):
        workspace = get_object_or_404(
            Workspace,
            project__org__slug=self.kwargs["org_slug"],
            project__slug=self.kwargs["project_slug"],
            name=self.kwargs["workspace_slug"],
        )

        if not has_permission(request.user, "job_request_pick_ref"):
            return redirect(workspace.get_jobs_url())

        if workspace.is_archived:
            msg = (
                "You cannot create Jobs for an archived Workspace."
                "Please contact an admin if you need to have it unarchved."
            )
            messages.error(request, msg)
            return redirect(workspace)

        # jobs need to be run on a backend so the user needs to have access to
        # at least one
        if not request.user.backends.exists():
            raise Http404

        response = functools.partial(
            TemplateResponse, request, "job_request_pick_ref.html"
        )

        try:
            commits = get_commits(
                workspace.repo_owner,
                workspace.repo_name,
            )
        except Exception as e:
            return response(context={"error": str(e), "workspace": workspace})

        commits = [
            {
                "sha": c["commit"]["tree"]["sha"],
                "message": first(c["commit"]["message"].split("\n")),
            }
            for c in commits
        ]
        return response(context={"commits": commits, "workspace": workspace})
