from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView, RedirectView, View
from django.views.generic.edit import FormMixin

from ..authorization import CoreDeveloper, has_permission, has_role
from ..forms import JobRequestSearchForm
from ..models import Backend, JobRequest, User, Workspace
from ..project import render_definition
from ..utils import raise_if_not_int


def filter_by_status(job_requests, status):
    """
    Filter JobRequests by status property

    JobRequest.status is built by "bubbling up" the status of each related Job.
    However, the construction of that property isn't easily converted to a
    QuerySet, hence this function.
    """
    if status not in ["failed", "running", "pending", "succeeded"]:
        # status is taken from a GET query arg so we need to treat it as user
        # input, returning the full JobRequest QuerySet if it's not a valid
        # value.
        return job_requests

    job_requests = job_requests.prefetch_related("jobs")
    return [r for r in job_requests if r.status.lower() == status]


class JobRequestCancel(View):
    def post(self, request, *args, **kwargs):
        try:
            job_request = JobRequest.objects.prefetch_related("jobs").get(
                pk=self.kwargs["pk"]
            )
        except JobRequest.DoesNotExist:
            raise Http404

        can_cancel_jobs = job_request.created_by == request.user or has_permission(
            request.user, "cancel_job", project=job_request.workspace.project
        )
        if not can_cancel_jobs:
            raise Http404

        if job_request.is_completed:
            return redirect(job_request)

        actions = list(set(job_request.jobs.values_list("action", flat=True)))
        job_request.cancelled_actions = actions
        job_request.save()

        return redirect(job_request)


class JobRequestDetail(DetailView):
    model = JobRequest
    queryset = JobRequest.objects.select_related(
        "created_by", "workspace"
    ).prefetch_related("jobs")
    template_name = "job_request_detail.html"

    def get_context_data(self, **kwargs):
        can_cancel_jobs = self.object.created_by == self.request.user or has_permission(
            self.request.user, "cancel_job", project=self.object.workspace.project
        )

        return super().get_context_data(**kwargs) | {
            "project_definition": mark_safe(
                render_definition(
                    escape(self.object.project_definition),
                    self.object.get_file_url,
                )
            ),
            "project_yaml_url": self.object.get_file_url("project.yaml"),
            "user_can_cancel_jobs": can_cancel_jobs,
        }


class JobRequestDetailRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        job_request = get_object_or_404(JobRequest, pk=self.kwargs["pk"])
        return job_request.get_absolute_url()


class JobRequestList(FormMixin, ListView):
    form_class = JobRequestSearchForm
    paginate_by = 25
    template_name = "job_request_list.html"

    def get_context_data(self, **kwargs):
        # only get Users created via GitHub OAuth
        users = User.objects.exclude(social_auth=None)
        users = sorted(users, key=lambda u: u.name.lower())

        workspaces = Workspace.objects.filter(is_archived=False).order_by("name")

        # filter object list based on status arg
        filtered_object_list = filter_by_status(
            self.object_list, self.request.GET.get("status")
        )
        context = super().get_context_data(object_list=filtered_object_list, **kwargs)

        context["backends"] = Backend.objects.order_by("slug")
        context["is_core_dev"] = has_role(self.request.user, CoreDeveloper)
        context["statuses"] = ["failed", "running", "pending", "succeeded"]
        context["users"] = {u.username: u.name for u in users}
        context["workspaces"] = workspaces
        return context

    def get_queryset(self):
        qs = (
            JobRequest.objects.prefetch_related("jobs")
            .select_related("backend", "workspace")
            .order_by("-pk")
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
