from django.core.management.base import BaseCommand
from pipeline import load_pipeline
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
            jobs = job_request.jobs.filter(run_command="")

            if not jobs.exists():
                # skip job requests where all jobs have already been processed,
                # making it quicker to rerun this script
                continue

            # load job_request's project_definition into pipeline and get the
            # command for this job
            try:
                pipeline = load_pipeline(job_request.project_definition)
            except Exception:
                print(f"{job_request.pk}: invalid config")
                continue  # we don't have a valid config

            for job in jobs:
                if action := pipeline.actions.get(job.action):
                    command = action.run.raw
                else:
                    continue  # unknown action, likely __error__

                # remove newlines and extra spaces
                job.run_command = command.replace("\n", "").replace("  ", " ")
                job.save()
