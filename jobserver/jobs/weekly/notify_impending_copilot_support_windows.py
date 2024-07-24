import sys

from django_extensions.management.jobs import WeeklyJob
from sentry_sdk.crons.decorator import monitor

from jobserver.copiloting import notify_impending_copilot_windows_closing
from services.sentry import monitor_config


class Job(WeeklyJob):
    help = "Notify slack of impending co-pilot support windows ending"  # noqa: A003

    @monitor(
        monitor_slug="notify_impending_copilot_support_windows",
        monitor_config=monitor_config("weekly"),
    )
    def execute(self):
        try:
            notify_impending_copilot_windows_closing()
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
