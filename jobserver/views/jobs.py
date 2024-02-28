import os

from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import RedirectView, View
from furl import furl

from .. import honeycomb
from ..authorization import CoreDeveloper, has_permission, has_role
from ..models import Job, JobRequest


class JobCancel(View):
    def post(self, request, *args, **kwargs):
        job = get_object_or_404(Job, identifier=self.kwargs["identifier"])

        can_cancel_job = job.job_request.created_by == request.user or has_permission(
            request.user, "job_cancel", project=job.job_request.workspace.project
        )
        if not can_cancel_job:
            raise Http404

        if job.is_completed or job.action in job.job_request.cancelled_actions:
            return redirect(job)

        job.job_request.cancelled_actions.append(job.action)
        job.job_request.save()

        messages.success(
            request, f'Your request to cancel "{job.action}" was successful'
        )

        return redirect(job)


class JobDetail(View):
    def get(self, request, *args, **kwargs):
        try:
            job = Job.objects.select_related(
                "job_request", "job_request__backend", "job_request__workspace"
            ).get(
                job_request__workspace__project__slug=self.kwargs["project_slug"],
                job_request__workspace__name=self.kwargs["workspace_slug"],
                job_request__pk=self.kwargs["pk"],
                identifier__startswith=self.kwargs["identifier"],
            )
        except (Job.DoesNotExist, MultipleObjectsReturned):
            raise Http404

        if job.identifier != self.kwargs["identifier"]:
            # redirect to the full URL if a partial identifier was used
            return redirect(job)

        can_cancel_jobs = job.job_request.created_by == request.user or has_permission(
            request.user, "job_cancel", project=job.job_request.workspace.project
        )

        honeycomb_can_view_links = has_role(self.request.user, CoreDeveloper)

        # we need all HTML to be in HTML files, so we built this here and make
        # use of it in the template rather than looking it up with a templatetag
        # (previously status_tools).  It isn't ideal to have here but until we
        # have more than one backend-specific error code it makes sense to keep
        # things together.
        log_path = ""
        log_path_url = ""
        if job.job_request.backend.slug == "tpp" and job.status_code == "nonzero_exit":
            log_path = os.path.join(
                job.job_request.backend.parent_directory,
                job.job_request.workspace.name,
                "metadata",
                f"{job.action}.log",
            )
            url = (
                furl(job.job_request.workspace.get_files_url())
                / "metadata"
                / f"{job.action}.log"
            )
            url.path.normalize()
            log_path_url = url.url

        honeycomb_links = {}
        if honeycomb_can_view_links:
            trace_link = honeycomb.trace_link(job)
            if trace_link:  # pragma: no cover
                honeycomb_links["Job Trace"] = trace_link
            honeycomb_links["Status and Resources"] = honeycomb.status_link(job)

            # Look this up manually, because if we use job.job_request, the
            # JobRequest will not have prefetched all associated Jobs, and
            # we will be unable to use JobRequest.completed_at (as it relies on
            # JobRequest.status)
            job_request = JobRequest.objects.filter(
                jobs__identifier=job.identifier
            ).first()

            honeycomb_links["Job Request"] = honeycomb.jobrequest_link(job_request)
            honeycomb_links["Previous runs of this action"] = (
                honeycomb.previous_actions_link(job)
            )

        previous_job = Job.objects.previous(job)
        code_compare_url = (
            job.job_request.workspace.repo.get_compare_url(
                previous_job.job_request.sha, job.job_request.sha
            )
            if previous_job
            else None
        )

        previous_suceeded_job = Job.objects.previous(job, filter_succeeded=True)
        code_compare_succeeded_url = (
            job.job_request.workspace.repo.get_compare_url(
                previous_suceeded_job.job_request.sha, job.job_request.sha
            )
            if previous_suceeded_job
            else None
        )

        context = {
            "cancellation_requested": job.action in job.job_request.cancelled_actions,
            "job": job,
            "log_path": log_path,
            "log_path_url": log_path_url,
            "object": job,
            "user_can_cancel_jobs": can_cancel_jobs,
            "view": self,
            "honeycomb_links": honeycomb_links,
            "code_compare_url": code_compare_url,
            "code_compare_succeeded_url": code_compare_succeeded_url,
        }

        return TemplateResponse(request, "job/detail.html", context=context)


class JobDetailRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        job = get_object_or_404(Job, identifier=self.kwargs["identifier"])
        return job.get_absolute_url()
