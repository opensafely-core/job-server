from django.core.management.base import BaseCommand
from pipeline import ProjectValidationError, load_pipeline
from rich.progress import track

from jobserver.models import JobRequest


class Command(BaseCommand):
    def handle(self, *args, **options):
        job_requests = JobRequest.objects.exclude(
            project_definition=""
        ).prefetch_related("jobs")

        count = job_requests.count()
        total = JobRequest.objects.count()
        print(f"Processing: {count}/{total}")

        for job_request in track(job_requests, description="Processing..."):
            # load job_request's project_definition into pipeline and get the
            # command for this job
            try:
                pipeline = load_pipeline(job_request.project_definition)
            except ProjectValidationError:
                print(f"{job_request.pk}: invalid config")
                continue  # we don't have a valid config

            for job in job_request.jobs.all():
                if action := pipeline.actions.get(job.action):
                    command = action.run.run
                else:
                    continue  # unknown action, likely __error__

                # remove newlines and extra spaces
                job.run_command = command.replace("\n", "").replace("  ", " ")
                job.save()
