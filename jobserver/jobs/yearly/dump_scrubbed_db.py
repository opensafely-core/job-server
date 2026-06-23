import os
import subprocess
import tempfile

import structlog
from django.conf import settings
from django_extensions.management.jobs import JobError, YearlyJob


logger = structlog.get_logger(__name__)


class Job(YearlyJob):
    help = "Scrubbed database dump job (in progress)"

    def execute(self):
        readonly_database = settings.DATABASES.get("readonly")
        data_scrubbing_database = settings.DATABASES.get("data_scrubbing")

        if readonly_database is None:
            raise JobError("JOBSERVER_READONLY_DATABASE_URL is not set")

        if data_scrubbing_database is None:
            raise JobError("JOBSERVER_SCRUBBED_DATABASE_URL is not set")

        with tempfile.NamedTemporaryFile(suffix=".dump") as raw_dump:
            logger.info(
                "Creating raw dump of readonly jobserver database", path=raw_dump.name
            )
            dump_database(readonly_database, raw_dump.name)
            logger.info(
                "Finished creating raw dump of readonly jobserver database",
                path=raw_dump.name,
            )
            try:
                logger.info("Restoring dump into data scrubbing database")
                restore_database(data_scrubbing_database, raw_dump.name)
                logger.info("Finished restoring dump into database")
            finally:
                logger.info("Clearing data scrubbing database")
                clear_database(data_scrubbing_database)
                logger.info("Finished clearing data scrubbing database")


def database_connection_args(database_config):
    return [
        "--host",
        database_config["HOST"],
        "--port",
        str(database_config["PORT"]),
        "--username",
        database_config["USER"],
        "--dbname",
        database_config["NAME"],
    ]


def dump_database(database_config, output):
    subprocess.run(
        [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            f"--file={output}",
            *database_connection_args(database_config),
        ],
        env={**os.environ, "PGPASSWORD": database_config["PASSWORD"]},
        check=True,
    )


def restore_database(database_config, input_dump):
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-acl",
            "--no-owner",
            *database_connection_args(database_config),
            input_dump,
        ],
        env={**os.environ, "PGPASSWORD": database_config["PASSWORD"]},
        check=True,
    )


def clear_database(database_config):
    subprocess.run(
        [
            "psql",
            *database_connection_args(database_config),
            "--command",
            "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
        ],
        env={**os.environ, "PGPASSWORD": database_config["PASSWORD"]},
        check=True,
    )
