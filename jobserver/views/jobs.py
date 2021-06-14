from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from ..models import Job
from ..roles import can_run_jobs


@method_decorator(user_passes_test(can_run_jobs), name="dispatch")
class JobCancel(View):
    def post(self, request, *args, **kwargs):
        job = get_object_or_404(Job, identifier=self.kwargs["identifier"])

        if job.is_finished or job.action in job.job_request.cancelled_actions:
            return redirect(job)

        job.job_request.cancelled_actions.append(job.action)
        job.job_request.save()
        return redirect(job)


class JobDetail(View):
    def get(self, request, *args, **kwargs):
        try:
            job = Job.objects.select_related(
                "job_request", "job_request__backend", "job_request__workspace"
            ).get(identifier__startswith=self.kwargs["identifier"])
        except (Job.DoesNotExist, MultipleObjectsReturned):
            raise Http404

        if job.identifier != self.kwargs["identifier"]:
            # redirect to the full URL if a partial identifier was used
            return redirect(job)

        context = {
            "job": job,
            "object": job,
            "user_can_run_jobs": can_run_jobs(self.request.user),
            "view": self,
        }

        return TemplateResponse(request, "job_detail.html", context=context)
