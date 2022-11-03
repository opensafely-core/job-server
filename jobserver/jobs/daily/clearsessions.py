from django.core.management import call_command
from django_extensions.management.jobs import DailyJob


class Job(DailyJob):
    help = "Run the clearsessions management command"  # noqa: A003

    def execute(self):
        call_command("clearsessions")
