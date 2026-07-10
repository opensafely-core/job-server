import os
import pathlib
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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


# This command creates a raw JobServer database dump containing personal data.
# Follow the personal data copying policy before running it. Only create or
# download a raw dump when agreed with your line manager or Tech SLT.
class Command(BaseCommand):
    help = (
        "Create a raw dump of the JobServer database. "
        "Only run this when agreed with your line manager or Tech SLT."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=settings.RAW_DATABASE_DUMP_PATH,
            help="Path where the raw database dump should be written",
        )

    def handle(self, *args, **options):
        database_config = settings.DATABASES["default"]
        output_path = pathlib.Path(options["output"])

        command = [
            "pg_dump",
            "--format=c",
            "--no-acl",
            "--no-owner",
            f"--file={output_path}",
            *database_connection_args(database_config),
        ]

        self.stdout.write(f"Creating raw JobServer database dump at {output_path}")

        try:
            subprocess.run(
                command,
                env={
                    "PATH": os.environ["PATH"],
                    "PGPASSWORD": database_config["PASSWORD"],
                },
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            raise CommandError(
                "pg_dump failed\n"
                f"returncode={error.returncode}\n"
                f"stdout={error.stdout}\n"
                f"stderr={error.stderr}"
            ) from error

        self.stdout.write(
            f"Finished creating raw JobServer database dump at {output_path}"
        )
