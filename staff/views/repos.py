import textwrap
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
from jobserver.models import Job, Org, Project, Repo, User


logger = structlog.get_logger(__name__)


def ran_at(job):
    if job is None:
        return

    return job.started_at or job.created_at


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoDetail(View):
    get_github_api = staticmethod(_get_github_api)

    def get(self, request, *args, **kwargs):
        repo = get_object_or_404(Repo, url=unquote(self.kwargs["repo_url"]))

        api_repo = self.get_github_api().get_repo(repo.owner, repo.name)

        workspaces = repo.workspaces.select_related(
            "signed_off_by", "created_by", "project", "project__org"
        ).order_by("name")
        projects = (
            Project.objects.filter(workspaces__in=workspaces)
            .distinct()
            .order_by("name")
        )
        users = User.objects.filter(job_requests__workspace__in=workspaces).distinct()

        jobs = Job.objects.filter(
            job_request__workspace__project__in=projects
        ).annotate(first_run=Min(Least("started_at", "created_at")))
        first_job_ran_at = ran_at(jobs.order_by("first_run").first())
        last_job_ran_at = ran_at(jobs.order_by("-first_run").first())
        num_signed_off = sum(1 for w in workspaces if w.signed_off_at)

        twelve_month_limit = first_job_ran_at + timedelta(days=365)

        def build_workspace(workspace, all_users):
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
                all_users.filter(job_requests__workspace=workspace)
                .distinct()
                .order_by(Lower("username"), Lower("fullname"))
            )
            if workspace.created_by not in users:
                users = [workspace.created_by, *users]

            return {
                "signed_off_at": workspace.signed_off_at,
                "signed_off_by": workspace.signed_off_by,
                "created_by": workspace.created_by,
                "get_staff_url": workspace.get_staff_url,
                "is_archived": workspace.is_archived,
                "job_requesting_users": users,
                "name": workspace.name,
            }

        workspaces = [build_workspace(w, users) for w in workspaces]

        def build_contact(user):
            return (
                f"{user.fullname} <{user.notifications_email}>"
                if user.fullname
                else user.notifications_email
            )

        contacts = "; ".join({build_contact(w["created_by"]) for w in workspaces})

        @define
        class Disabled:
            already_signed_off: bool
            no_permission: bool
            not_ready: bool

            def __bool__(self):
                # gather the outcome of all the instance vars to define the
                # boolean state of the whole object
                return any(
                    [self.already_signed_off, self.no_permission, self.not_ready]
                )

        can_sign_off = has_permission(request.user, "repo_sign_off_with_outputs")
        disabled = Disabled(
            already_signed_off=repo.internal_signed_off_at is not None,
            no_permission=repo.has_github_outputs and not can_sign_off,
            not_ready=repo.researcher_signed_off_at is None,
        )

        context = {
            "contacts": contacts,
            "first_job_ran_at": first_job_ran_at,
            "disabled": disabled,
            "last_job_ran_at": last_job_ran_at,
            "num_signed_off": num_signed_off,
            "projects": projects,
            "repo": {
                "created_at": api_repo["created_at"],
                "has_github_outputs": repo.has_github_outputs,
                "internal_signed_off_at": repo.internal_signed_off_at,
                "is_private": api_repo["private"],
                "get_staff_sign_off_url": repo.get_staff_sign_off_url(),
                "name": repo.name,
                "owner": repo.owner,
                "researcher_signed_off_at": repo.researcher_signed_off_at,
                "url": repo.url,
            },
            "twelve_month_limit": twelve_month_limit,
            "workspaces": workspaces,
        }

        return TemplateResponse(
            request,
            "staff/repo_detail.html",
            context=context,
        )


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class RepoList(ListView):
    model = Repo
    template_name = "staff/repo_list.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "orgs": Org.objects.order_by(Lower("name")),
            "q": self.request.GET.get("q", ""),
        }

    def get_queryset(self):
        qs = Repo.objects.order_by(Lower("url"))

        # filter on the search query
        if q := self.request.GET.get("q"):
            qs = qs.filter(url__icontains=q)

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

        body = f"""
        The [{repo.name}]({repo.url}) repo is ready to be made public.

        This repo has been checked and approved by {request.user.name}.

        An owner of the `opensafely` org is required to make this change, they can do so on the [repo settings page]({repo.url}/settings).
        """

        with transaction.atomic():
            data = self.get_github_api().create_issue(
                "ebmdatalab",
                "tech-support",
                f"Switch {repo.name} repo to public",
                textwrap.dedent(body),
                [],
            )
            issue_url = data["html_url"]

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
