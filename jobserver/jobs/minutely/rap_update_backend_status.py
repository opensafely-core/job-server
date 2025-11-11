from django.core.management import call_command
from django_extensions.management.jobs import MinutelyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


class Job(MinutelyJob):
    help = "Run the rap_update_backend_status management command"  # noqa: A003

    @monitor(
        monitor_slug="rap_update_backend_status",
        monitor_config=monitor_config(
            "* * * * *",
            checkin_margin=1,
            max_runtime=1,
            failure_issue_threshold=10,
            recovery_threshold=1,
        ),
    )
    def execute(self):
        call_command("rap_update_backend_status")
