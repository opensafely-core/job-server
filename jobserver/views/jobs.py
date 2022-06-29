from datetime import timedelta

from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import RedirectView, View

from ..authorization import CoreDeveloper, has_permission, has_role
from ..models import Job


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
        return redirect(job)


class JobDetail(View):
    def get(self, request, *args, **kwargs):
        try:
            job = Job.objects.select_related(
                "job_request", "job_request__backend", "job_request__workspace"
            ).get(
                job_request__workspace__project__org__slug=self.kwargs["org_slug"],
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

        # Add arbitrary small timedeltas to the start and end times.
        # If we use the exact start and end times of a job, we do not
        # reliably see the first and last honeycomb events relating to that job.
        # This could be due to clock skew, '>' rather than '>=' comparators
        # and/or other factors.
        honeycomb_context_starttime = job.created_at - timedelta(minutes=1)

        honeycomb_context_endtime = timezone.now()
        if job.completed_at is not None:
            honeycomb_context_endtime = job.completed_at + timedelta(minutes=3)

        context = {
            "job": job,
            "object": job,
            "user_can_cancel_jobs": can_cancel_jobs,
            "view": self,
            "honeycomb_can_view_links": honeycomb_can_view_links,
            "honeycomb_context_starttime": honeycomb_context_starttime,
            "honeycomb_context_endtime": honeycomb_context_endtime,
        }

        return TemplateResponse(request, "job_detail.html", context=context)


class JobDetailRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        job = get_object_or_404(Job, identifier=self.kwargs["identifier"])
        return job.get_absolute_url()
