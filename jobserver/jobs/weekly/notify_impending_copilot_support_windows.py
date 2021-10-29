import sys

from django_extensions.management.jobs import WeeklyJob

from jobserver.copiloting import notify_impending_copilot_windows_closing


class Job(WeeklyJob):
    help = "Notify slack of impending co-pilot support windows ending"  # noqa: A003

    def execute(self):
        try:
            notify_impending_copilot_windows_closing()
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
