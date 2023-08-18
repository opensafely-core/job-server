from datetime import timedelta
from urllib.parse import unquote

import structlog
from attrs import define
from django.contrib import messages
from django.db import transaction
from django.db.models import Min
from django.db.models.functions import Least, Lower
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import ListView, View

from jobserver.authorization import CoreDeveloper, has_permission
from jobserver.authorization.decorators import require_role
from jobserver.github import _get_github_api
from jobserver.issues import create_switch_repo_to_public_request
from jobserver.models import Job, Org, Project, Repo, User

from .qwargs_tools import qwargs


logger = structlog.get_logger(__name__)


@define
class Disabled:
    already_signed_off: bool
    no_permission: bool
    not_ready: bool

    def __bool__(self):
        # gather the outcome of all the instance vars to define the
        # boolean state of the whole object
        return any([self.already_signed_off, self.no_permission, self.not_ready])


def ran_at(job):
    if job is None:
        return

    return job.started_at or job.created_at


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def build_contacts(self, workspaces):
        def build_contact(user):
            return f"{user.fullname} <{user.email}>" if user.fullname else user.email

        return "; ".join({build_contact(w.created_by) for w in workspaces})

    def build_dates(self, api_repo, projects):
        jobs = Job.objects.filter(
            job_request__workspace__project__in=projects
        ).annotate(first_run=Min(Least("started_at", "created_at")))

        first_job_ran_at = ran_at(jobs.order_by("first_run").first())
        last_job_ran_at = ran_at(jobs.order_by("-first_run").first())
        twelve_month_limit = first_job_ran_at + timedelta(days=365)

        return {
            "first_job_ran_at": first_job_ran_at,
            "last_job_ran_at": last_job_ran_at,
            "repo_created_at": api_repo["created_at"],
            "twelve_month_limit": twelve_month_limit,
        }

    def build_disabled(self, repo, user):
        can_sign_off = has_permission(user, "repo_sign_off_with_outputs")
        return Disabled(
            already_signed_off=repo.internal_signed_off_at is not None,
            no_permission=repo.has_github_outputs and not can_sign_off,
            not_ready=repo.researcher_signed_off_at is None,
        )

    def build_repo(self, api_repo, db_repo):
        return {
            "has_github_outputs": db_repo.has_github_outputs,
            "internal_signed_off_at": db_repo.internal_signed_off_at,
            "is_private": api_repo["private"],
            "get_staff_sign_off_url": db_repo.get_staff_sign_off_url(),
            "name": db_repo.name,
            "owner": db_repo.owner,
            "researcher_signed_off_at": db_repo.researcher_signed_off_at,
            "url": db_repo.url,
        }

    def build_workspaces(self, workspaces):
        for workspace in workspaces:
            """
            Build a dictionary representation of the Workspace data for the template

            We want to show a list of users-who-created-jobs-in-this-workspace
            in the template.  Getting this as part of the Workspace QuerySet
            doesn't appear to be possible (we tried Subquery and Prefetch to no
            avail).  Instead we've looked up the users who created jobs for
            each workspace used in this view and are pairing them up here.
            """

            # get the users who created jobs in this workspace or created it,
            # just in case the creator has not run any jobs.
            users = list(
                User.objects.filter(job_requests__workspace=workspace)
                .distinct()
                .order_by(Lower("username"), Lower("fullname"))
            )
            if workspace.created_by not in users:
                users = [workspace.created_by, *users]

            yield {
                "signed_off_at": workspace.signed_off_at,
                "signed_off_by": workspace.signed_off_by,
                "created_by": workspace.created_by,
                "get_staff_url": workspace.get_staff_url,
                "is_archived": workspace.is_archived,
                "job_requesting_users": users,
                "name": workspace.name,
            }

    def get(self, request, *args, **kwargs):
        repo = get_object_or_404(Repo, url=unquote(self.kwargs["repo_url"]))

        api_repo = self.get_github_api().get_repo(repo.owner, repo.name)

        workspaces = repo.workspaces.select_related(
            "signed_off_by", "created_by", "project"
        ).order_by("name")
        projects = (
            Project.objects.filter(workspaces__in=workspaces)
            .distinct()
            .order_by("name")
        )

        num_signed_off = sum(1 for w in workspaces if w.signed_off_at)

        context = {
            "contacts": self.build_contacts(workspaces),
            "dates": self.build_dates(api_repo, projects),
            "disabled": self.build_disabled(repo, request.user),
            "num_signed_off": num_signed_off,
            "projects": projects,
            "repo": self.build_repo(api_repo, repo),
            "workspaces": list(self.build_workspaces(workspaces)),
        }

        return TemplateResponse(
            request,
            "staff/repo/detail.html",
            context=context,
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoList(ListView):
    model = Repo
    template_name = "staff/repo/list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "orgs": Org.objects.order_by(Lower("name")),
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = Repo.objects.order_by(Lower("url"))

        # filter on the search query
        if q := self.request.GET.get("q"):
            fields = [
                "url",
            ]
            qs = qs.filter(qwargs(fields, q))

        if has_outputs := self.request.GET.get("has_outputs") == "yes":
            qs = qs.filter(has_github_outputs=has_outputs)

        if org := self.request.GET.get("org"):
            qs = qs.filter(workspaces__project__org__slug=org)

        return qs.distinct()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoSignOff(View):
    get_github_api = staticmethod(_get_github_api)

    def post(self, request, *args, **kwargs):
        repo = get_object_or_404(Repo, url=unquote(self.kwargs["repo_url"]))

        if repo.has_github_outputs and not has_permission(
            request.user, "repo_sign_off_with_outputs"
        ):
            msg = "The SignOffRepoWithOutputs role is required to sign off repos with outputs hosted on GitHub"
            messages.error(request, msg)
            return redirect(repo.get_staff_url())

        with transaction.atomic():
            issue_url = create_switch_repo_to_public_request(
                repo,
                request.user,
                self.get_github_api(),
            )

            repo.internal_signed_off_at = timezone.now()
            repo.internal_signed_off_by = request.user
            repo.save()

            tech_support_url = f'<a href="{issue_url}">ticket has been created</a>'
            messages.success(
                request,
                mark_safe(
                    f"A {tech_support_url} for tech-support, they have been notified in #tech-support-channel",
                ),
            )

        return redirect(repo.get_staff_url())
