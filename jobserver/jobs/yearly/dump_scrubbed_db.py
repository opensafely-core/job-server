import os
import pathlib
import subprocess

import structlog
from django.conf import settings
from django_extensions.management.jobs import YearlyJob


logger = structlog.get_logger(__name__)


class Job(YearlyJob):
    help = "Scrubbed database dump job (in progress)"

    def execute(self):
        raw_dump = pathlib.Path("/tmp/jobserver_raw.dump")
        readonly_db = settings.DATABASES.get("readonly")
        scrubbed_db = settings.DATABASES.get("scrubbed")

        if readonly_db is None:
            raise RuntimeError("JOBSERVER_READONLY_DATABASE_URL is not found")

        if scrubbed_db is None:
            raise RuntimeError("JOBSERVER_SCRUBBED_DATABASE_URL is not found")

        try:
            logger.info("Creating raw dump of readonly jobserver database")
            dump_database(readonly_db, raw_dump)

            logger.info("Restoring dump into scrubbed jobserver database")
            restore_database(scrubbed_db, raw_dump)

            logger.info("Finished restoring dump into database")

        finally:
            logger.info("Deleting temporary source dump")
            raw_dump.unlink(missing_ok=True)


def database_url(db):
    return f"postgresql://{db['USER']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"


def dump_database(db, output):
    subprocess.run(
        [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            f"--file={output}",
            database_url(db),
        ],
        env={**os.environ, "PGPASSWORD": db["PASSWORD"]},
        check=True,
    )


def restore_database(db, input_dump):
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-acl",
            "--no-owner",
            "--dbname",
            database_url(db),
            str(input_dump),
        ],
        env={**os.environ, "PGPASSWORD": db["PASSWORD"]},
        check=True,
    )
