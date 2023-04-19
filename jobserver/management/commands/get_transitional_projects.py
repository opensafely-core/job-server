import csv
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from furl import furl

from jobserver.models import Job, Project


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Get "transitional" projects

        We're defining transitional projects by a few criteria and this command
        tries to make that clear and easy to change for the next person who
        needs to work on it.

        Our current definition is:

            Any project which has run jobs in the last 6 months

        """
        # Python's timedelta doesn't handle months so we're treating them as 30
        # days long.
        six_months_ago = timezone.now() - timedelta(days=30 * 6)

        # only look at projects with jobs which have been started in the last 6 months
        #
        # Note: the __date portion of this epic filter casts the started_at
        # value to a date so even though we're passing in a datetime the ORM
        # does the right thing for us and passes down just the date portion of
        # six_months_ago so we can get 6mo ago for all of the target day.
        projects = (
            Project.objects.filter(
                workspaces__job_requests__jobs__started_at__date__gte=six_months_ago
            )
            .distinct()
            .order_by("number")
        )

        data = []
        for project in projects:
            name = project.name
            number = project.number
            latest_job_started_at = (
                Job.objects.filter(job_request__workspace__project=project)
                .exclude(started_at=None)
                .order_by("-started_at")
                .first()
                .started_at.isoformat()
            )
            org = project.org.name

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

        with open("transitional-projects.csv", "w") as f:
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
