import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from furl import furl

from jobserver.models import Job, Project


class Command(BaseCommand):
    def handle(self, *args, **options):
        data = []
        for project in Project.objects.order_by("number", "name"):
            name = project.name
            number = project.number
            org = project.org.name

            latest_job = (
                Job.objects.filter(job_request__workspace__project=project)
                .exclude(started_at=None)
                .order_by("-started_at")
                .first()
            )
            if latest_job and latest_job.started_at:
                latest_job_started_at = latest_job.started_at.isoformat()
            else:
                latest_job_started_at = None

            if number:
                url = f"https://www.opensafely.org/approved-projects#project-{number}"
            else:
                url = furl(settings.BASE_URL) / project.get_staff_url()

            # print for local debugging
            print(number, name, org, latest_job_started_at, url)

            data.append(
                {
                    "number": number,
                    "name": name,
                    "latest_job_started_at": latest_job_started_at,
                    "org": org,
                    "url": url,
                }
            )

        with open("all-projects.csv", "w") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "number",
                    "name",
                    "latest_job_started_at",
                    "org",
                    "url",
                ],
            )

            writer.writeheader()
            writer.writerows(data)
