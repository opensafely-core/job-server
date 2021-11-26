import pathlib
import subprocess
import sys

from django_extensions.management.jobs import HourlyJob
from environs import Env


env = Env()


class Job(HourlyJob):
    help = "Dump the database to storage for copying to local dev environments"  # noqa: A003

    def execute(self):
        database_url = env.str("DATABASE_URL")
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
                "--file={output}",
                database_url,
            ],
        )
