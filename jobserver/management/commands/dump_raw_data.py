"""Django management command to create a raw database dump.

Read this docstring before using this command!

Usually developers should instead use the scrubbed database dump if they need
near-realistic production data for use in their development process. Some
investigations or tasks may need to use the raw database dump in exceptional
circumstances.

If you think you need to use this you must follow the [personal data copying
policy]. That means you must:

- decide whether you really need to copy it or if you could achieve your goal
  in a different way;
- discuss your plans with your line manager or the Tech SLT if they are not
  available;
- record your decision in the [personal data copying decision log] if
  you go ahead.
- remove the raw dump from the server and developer machines as soon as it is
  no longer required.

[personal data copying policy]: https://bennett.wiki/tech-group/policies/personal-data-copying-policy/#personal-data-copying-policy
[personal data copying decision log]: https://docs.google.com/spreadsheets/d/1C1z3WV-WSL-H1keZZCVPm6hR_5ajjgRT5zGO5cLv2Aw
"""

import os
import pathlib
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from jobserver.slacks import alert_raw_dump


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


class Command(BaseCommand):
    help = (
        "Create a raw database dump. You must follow the personal data "
        "copying policy. Only run this when agreed with your line manager "
        "or Tech SLT. You must record your decision in the personal data "
        "copying decision log and remove the raw dump from the server and "
        "developer machines as soon as it is no longer required."
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
        alert_raw_dump()
