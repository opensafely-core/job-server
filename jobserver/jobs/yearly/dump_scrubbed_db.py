import os
import pathlib
import subprocess
import tempfile

import structlog
from django.conf import settings
from django.core.management import CommandError, call_command
from django_extensions.management.jobs import JobError, YearlyJob


logger = structlog.get_logger(__name__)


class Job(YearlyJob):
    help = "Scrubbed database dump job (in progress)"

    def execute(self):
        scrubbed_dump_path = settings.SCRUBBED_DATABASE_DUMP_PATH
        readonly_database = settings.DATABASES.get(settings.READONLY_DATABASE_ALIAS)
        data_scrubbing_database = settings.DATABASES.get(
            settings.DATA_SCRUBBING_DATABASE_ALIAS
        )

        if readonly_database is None:
            raise JobError("JOBSERVER_READONLY_DATABASE_URL is not set")

        if data_scrubbing_database is None:
            raise JobError("JOBSERVER_SCRUBBING_DATABASE_URL is not set")

        with tempfile.TemporaryDirectory(
            prefix="dump-scrubbed-db-", dir=scrubbed_dump_path.parent
        ) as temp_dir_path:
            temp_dir_path = pathlib.Path(temp_dir_path)
            raw_dump_path = temp_dir_path / "raw.dump"
            temp_scrubbed_dump_path = temp_dir_path / scrubbed_dump_path.name
            dump_database(readonly_database, raw_dump_path)
            try:
                restore_database(data_scrubbing_database, raw_dump_path)
                scrub_database(settings.DATA_SCRUBBING_DATABASE_ALIAS)
                dump_database(data_scrubbing_database, temp_scrubbed_dump_path)
                temp_scrubbed_dump_path.replace(scrubbed_dump_path)
            finally:
                clear_database(data_scrubbing_database)


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


def run_database_command(command, database_config):
    logger.info("Running database command", command=command)

    try:
        subprocess.run(
            command,
            env={"PATH": os.environ["PATH"], "PGPASSWORD": database_config["PASSWORD"]},
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise JobError(
            f"{command[0]} failed\n"
            f"returncode={error.returncode}\n"
            f"stdout={error.stdout}\n"
            f"stderr={error.stderr}"
        ) from error


def dump_database(database_config, dump_file_path):
    logger.info("Creating database dump", path=dump_file_path)
    run_database_command(
        [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            f"--file={dump_file_path}",
            *database_connection_args(database_config),
        ],
        database_config,
    )
    logger.info("Finished creating database dump", path=dump_file_path)


def restore_database(database_config, dump_file_path):
    logger.info(
        "Restoring database dump", path=dump_file_path, database=database_config["NAME"]
    )
    run_database_command(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-acl",
            "--no-owner",
            *database_connection_args(database_config),
            dump_file_path,
        ],
        database_config,
    )
    logger.info(
        "Finished restoring dump into database",
        path=dump_file_path,
        database=database_config["NAME"],
    )


def scrub_database(database_alias):
    logger.info("Scrubbing database", database=database_alias)
    try:
        call_command("scrub_data", database_alias)
    except CommandError as error:
        raise JobError(f"Scrubbing failed: {error}") from error
    logger.info("Finished scrubbing database", database=database_alias)


def clear_database(database_config):
    logger.info("Clearing database", database=database_config["NAME"])
    run_database_command(
        [
            "psql",
            *database_connection_args(database_config),
            "--command",
            "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
        ],
        database_config,
    )
    logger.info("Finished clearing database", database=database_config["NAME"])
