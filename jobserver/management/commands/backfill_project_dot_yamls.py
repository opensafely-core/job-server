from django.core.management.base import BaseCommand

from ...github import get_file
from ...models import JobRequest


class Command(BaseCommand):
    def handle(self, *args, **options):
        job_requests = JobRequest.objects.filter(project_definition="").order_by("-pk")

        for job_request in job_requests:
            try:
                content = get_file(job_request.workspace.repo_name, job_request.sha)
            except Exception as e:
                print(
                    f"JobRequest={job_request.pk} | Failed to get project.yaml with error: {e}"
                )
                continue

            if content is None:
                print(f"JobRequest={job_request.pk} | No project.yaml found")
                continue

            # this is a best effort backfill, we don't care if the branch has gone away for instance
            job_request.project_definition = content
            job_request.save()
