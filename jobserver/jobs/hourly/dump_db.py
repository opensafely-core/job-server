import pathlib
import subprocess
import sys

from django.conf import settings
from django_extensions.management.jobs import HourlyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


class Job(HourlyJob):
    help = "Dump the database to storage for copying to local dev environments"  # noqa: A003

    @monitor(monitor_slug="dump_db", monitor_config=monitor_config("hourly"))
    def execute(self):
        db = settings.DATABASES["default"]
        output = pathlib.Path("/storage/jobserver.dump")

        if not output.exists():
            print(f"Unknown output path: {output}", file=sys.stderr)
            sys.exit(1)

        # We use the "custom" output format for pg_dump to get smaller
        # files, the docs have more detail on why it can be useful:
        # https://www.postgresql.org/docs/14/app-pgdump.html
        subprocess.check_call(
            [
                "pg_dump",
                "--format=c",
                "--no-acl",
                "--no-owner",
                f"--file={output}",
                f"postgresql://{db['USER']}@{db['HOST']}:{db['PORT']}/{db['NAME']}",
            ],
            env={"PGPASSWORD": db["PASSWORD"]},
        )
