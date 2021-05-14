from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, View

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


class JobDetail(DetailView):
    slug_field = "identifier"
    slug_url_kwarg = "identifier"
    queryset = Job.objects.select_related(
        "job_request", "job_request__backend", "job_request__workspace"
    )
    template_name = "job_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_can_run_jobs"] = can_run_jobs(self.request.user)
        return context
