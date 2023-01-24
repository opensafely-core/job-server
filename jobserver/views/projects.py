import concurrent
import operator

import requests
from django.core.exceptions import PermissionDenied
from django.db.models import Min, OuterRef, Subquery
from django.db.models.functions import Least, Lower
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import UpdateView, View
from furl import furl

from ..authorization import has_permission
from ..github import _get_github_api
from ..models import Job, Project, Snapshot


# Create a global threadpool for getting repos.  This lets us have a single
# pool across all requests and saves the overhead from setting up threads on
# each request.
repo_thread_pool = concurrent.futures.ThreadPoolExecutor(thread_name_prefix="get_repo")


class ProjectDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

        can_create_workspaces = has_permission(
            request.user, "workspace_create", project=project
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
            project_org_in_user_orgs = project.org in request.user.orgs.all()

        job = (
            Job.objects.filter(job_request__workspace__project=project)
            .annotate(first_run=Min(Least("started_at", "created_at")))
            .order_by("first_run")
            .first()
        )
        if job:
            first_job_ran_at = job.started_at or job.created_at
        else:
            first_job_ran_at = None

        repo_urls = set(workspaces.values_list("repo__url", flat=True))
        all_repos = list(self.iter_repos(repo_urls))
        private_repos = sorted(
            (r for r in all_repos if r["is_private"] or r["is_private"] is None),
            key=operator.itemgetter("name"),
        )
        public_repos = sorted(
            (r for r in all_repos if r["is_private"] is False),
            key=operator.itemgetter("name"),
        )

        context = {
            "can_create_workspaces": can_create_workspaces,
            "first_job_ran_at": first_job_ran_at,
            "is_member": is_member,
            "memberships": memberships,
            "outputs": self.get_outputs(workspaces),
            "project": project,
            "private_repos": private_repos,
            "public_repos": public_repos,
            "project_org_in_user_orgs": project_org_in_user_orgs,
            "status": self.get_status(project),
            "workspaces": workspaces,
        }

        return TemplateResponse(request, "project_detail.html", context=context)

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
            .exclude(published_at=None)
            .order_by("-published_at")
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
            .select_related(
                "workspace", "workspace__project", "workspace__project__org"
            )
            .order_by("-published_at")
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

    def iter_repos(self, repo_urls):
        def get_repo(url):
            f = furl(url)

            try:
                is_private = self.get_github_api().get_repo_is_private(*f.path.segments)
            except requests.HTTPError:
                is_private = None

            return {
                "name": f.path.segments[1],
                "url": url,
                "is_private": is_private,
            }

        # use the threadpool to parallelise the repo requests
        yield from repo_thread_pool.map(get_repo, repo_urls, timeout=30)


class ProjectEdit(UpdateView):
    fields = [
        "status",
        "status_description",
    ]
    model = Project
    template_name = "project_edit.html"

    def get_object(self):
        project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        if not project.members.filter(username=self.request.user.username).exists():
            raise PermissionDenied

        return project

    def get_success_url(self):
        return self.request.GET.get("next") or self.object.get_absolute_url()
