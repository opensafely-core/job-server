from django.core.management import call_command
from django_extensions.management.jobs import DailyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


class Job(DailyJob):
    help = "Run the clearsessions management command"  # noqa: A003

    @monitor(monitor_slug="clearsessions", monitor_config=monitor_config("daily"))
    def execute(self):
        call_command("clearsessions")
