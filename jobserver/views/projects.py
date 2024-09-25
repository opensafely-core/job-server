import concurrent
import itertools
import operator

import requests
from django.core.exceptions import PermissionDenied
from django.db.models import Min, OuterRef, Subquery
from django.db.models.functions import Least, Lower
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import ListView, UpdateView, View
from markdown import markdown
from opentelemetry import context as otel_context
from opentelemetry import trace

from jobserver import html_utils
from jobserver.utils import set_from_qs

from ..authorization import has_permission, permissions
from ..github import _get_github_api
from ..models import Job, JobRequest, Project, PublishRequest, Repo, Snapshot


# Create a global threadpool for getting repos.  This lets us have a single
# pool across all requests and saves the overhead from setting up threads on
# each request.
repo_thread_pool = concurrent.futures.ThreadPoolExecutor(thread_name_prefix="get_repo")


class ProjectDetail(View):
    get_github_api = staticmethod(_get_github_api)
    tracer = trace.get_tracer_provider().get_tracer(__name__)

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, slug=self.kwargs["project_slug"])
        project.status_description = html_utils.clean_html(
            markdown(project.status_description)
        )

        can_create_workspaces = has_permission(
            request.user, permissions.workspace_create, project=project
        )

        is_member = project.members.filter(username=request.user.username).exists()

        memberships = project.memberships.select_related("user").order_by(
            Lower("user__fullname"), "user__username"
        )
        workspaces = project.workspaces.select_related("repo").order_by(
            "is_archived", "name"
        )

        project_org_in_user_orgs = False
        if request.user.is_authenticated:
            project_orgs = set_from_qs(project.orgs.all())
            user_orgs = set_from_qs(request.user.orgs.all())
            project_org_in_user_orgs = bool(project_orgs & user_orgs)

        with self.tracer.start_as_current_span("first_job_ran_at"):
            job = (
                Job.objects.filter(job_request__workspace__project=project)
                .only("pk", "job_request_id", "created_at", "started_at")
                .annotate(first_run=Min(Least("started_at", "created_at")))
                .order_by("first_run")
                .first()
            )
            if job:
                first_job_ran_at = job.started_at or job.created_at
            else:
                first_job_ran_at = None

        with self.tracer.start_as_current_span("repos"):
            repos = Repo.objects.filter(workspaces__in=workspaces).distinct()

            all_repos = list(self.iter_repos(repos, otel_context.get_current()))

            private_repos = sorted(
                (r for r in all_repos if r["is_private"] or r["is_private"] is None),
                key=operator.itemgetter("name"),
            )
            public_repos = sorted(
                (r for r in all_repos if r["is_private"] is False),
                key=operator.itemgetter("name"),
            )

        is_interactive_user = has_permission(
            request.user, permissions.analysis_request_create, project=project
        )

        with self.tracer.start_as_current_span("reports"):
            all_reports = project.reports.filter(
                publish_requests__decision=PublishRequest.Decisions.APPROVED
            ).order_by("-created_at")
            reports = all_reports[:5]

        counts = {
            "reports": all_reports.count(),
        }

        context = {
            "can_create_workspaces": can_create_workspaces,
            "counts": counts,
            "first_job_ran_at": first_job_ran_at,
            "is_interactive_user": is_interactive_user,
            "is_member": is_member,
            "memberships": memberships,
            "outputs": self.get_outputs(workspaces),
            "project": project,
            "private_repos": private_repos,
            "public_repos": public_repos,
            "project_org_in_user_orgs": project_org_in_user_orgs,
            "reports": reports,
            "status": self.get_status(project),
            "workspaces": workspaces,
        }

        return TemplateResponse(request, "project/detail.html", context=context)

    def get_outputs(self, workspaces):
        """
        Builds up a QuerySet of Snapshots (outputs) for the page

        We only want to show the most recent published Snapshot for each
        Workspace.
        """
        # build a Subquery to get the PK for the most recently published
        # Snapshot for each Workspace
        latest_snapshot_qs = (
            Snapshot.objects.filter(workspace_id=OuterRef("id"))
            .filter(publish_requests__decision=PublishRequest.Decisions.APPROVED)
            .order_by("-publish_requests__decision_at")
            .values("pk")[:1]
        )

        # annotate the subquery onto the Workspace QuerySet
        workspaces = workspaces.annotate(latest_snapshot=Subquery(latest_snapshot_qs))

        # build the QuerySet of Snapshots from the PKs annotated onto each Workspace
        snapshot_pks = workspaces.exclude(latest_snapshot=None).values_list(
            "latest_snapshot", flat=True
        )

        return (
            Snapshot.objects.filter(pk__in=snapshot_pks)
            .select_related("workspace", "workspace__project")
            .order_by("-publish_requests__decision_at")
        )

    def get_status(self, project):
        # break up the choice label into a title and optional sub title
        title, _, sub_title = project.get_status_display().partition(" - ")

        variants_lut = {
            "completed-and-awaiting": "success",
            "completed-and-linked": "success",
            "ongoing": "info",
            "ongoing-and-linked": "info",
            "postponed": "danger",
            "retired": "warning",
        }

        return {
            "title": title,
            "sub_title": sub_title,
            "variant": variants_lut[project.status],
        }

    def iter_repos(self, repos, ctx):
        def get_repo(repo, ctx):
            otel_context.attach(ctx)
            with self.tracer.start_as_current_span("get_repo"):
                try:
                    is_private = self.get_github_api().get_repo_is_private(
                        repo.owner, repo.name
                    )
                except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
                    is_private = None
                span = trace.get_current_span()
                span.set_attribute("repo_owner", repo.owner)
                span.set_attribute("repo_name", repo.name)
                span.set_attribute("repo_is_private", is_private)

                return {
                    "name": repo.name,
                    "url": repo.url,
                    "is_private": is_private,
                }

        # use the threadpool to parallelise the repo requests
        try:
            yield from repo_thread_pool.map(
                get_repo, repos, itertools.repeat(ctx), timeout=30
            )
        except TimeoutError:
            yield {"name": "GitHub API Unavailable", "is_private": None, "url": ""}


class ProjectEdit(UpdateView):
    fields = [
        "status",
        "status_description",
    ]
    model = Project
    template_name = "project/edit.html"

    def form_valid(self, form):
        project = form.save(commit=False)
        project.updated_by = self.request.user
        project.save()

        url = self.request.GET.get("next") or self.object.get_absolute_url()
        return redirect(url)

    def get_object(self):
        project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

        user = self.request.user
        user_has_project_manage = has_permission(
            user, permissions.project_manage, project=project
        )

        if not user_has_project_manage:
            raise PermissionDenied

        return project


class ProjectEventLog(ListView):
    paginate_by = 25
    template_name = "project/event_log.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "project": self.project,
        }

    def get_queryset(self):
        return (
            JobRequest.objects.with_started_at()
            .filter(workspace__project=self.project)
            .select_related("backend", "created_by", "workspace")
            .prefetch_related("workspace__project__orgs")
            .order_by("-pk")
        )


class ProjectReportList(ListView):
    template_name = "project/report_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs["project_slug"])

        self.can_view_unpublished_reports = has_permission(
            self.request.user, permissions.release_file_view, project=self.project
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "project": self.project,
            "user_can_view_unpublished_reports": self.can_view_unpublished_reports,
        }

    def get_queryset(self):
        reports = self.project.reports.order_by("-created_at")

        if not self.can_view_unpublished_reports:
            reports = reports.filter(
                publish_requests__decision=PublishRequest.Decisions.APPROVED
            )

        return reports
