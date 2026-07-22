"""
Quarter-hourly job to delete raw JobServer database dumps that have reached a certain
age.

Usually developers should use the scrubbed database dump if they need near-realistic
production data for use in their development process. Some investigations or  tasks
may need to use the raw database dump in exceptional circumstances. They are created
manually using the dump_raw_data management command when access has been  agreed and
recorded in accordance with the Personal Data Copying Policy.

The raw dump needs to remain available for long enough for an authorised developer to
download it. The developer who created the dump should delete it from the production
server as soon as it is no longer needed for the approved purpose. This job acts as a
backstop to delete dumps within a certain period, in case of manual error.

The age of the dump is determined from its modification time. Running this job every
15 minutes and deleting dumps that are at least 15 minutes old allows at least 15
minutes to download a dump while ensuring that it is automatically deleted within 30
minutes.

A raw database dump will not exist most of the time, so the dump not existing is not an
error.
"""

from datetime import UTC, datetime, timedelta

import structlog
from django.conf import settings
from django_extensions.management.jobs import JobError, QuarterHourlyJob
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


logger = structlog.get_logger(__name__)

RAW_DUMP_AGE_LIMIT = timedelta(minutes=15)
"""Delete files older than this when the job runs."""


class Job(QuarterHourlyJob):
    help = (
        "Delete raw database dumps that have reached the deletion age to limit the "
        "availability of production data"
    )

    @monitor(
        monitor_slug="delete_raw_dump", monitor_config=monitor_config("*/15 * * * *")
    )
    def execute(self):
        raw_dump_path = settings.RAW_DATABASE_DUMP_PATH

        if not raw_dump_path.exists():
            logger.info("Raw database dump does not exist", path=raw_dump_path)
            return

        if not raw_dump_path.is_file():
            raise JobError(f"Raw database dump path is not a file: {raw_dump_path}")

        # Use the file's last-modified time as an approximation of when the dump
        # finished being written, and convert it to UTC datetime.
        modified_at = datetime.fromtimestamp(raw_dump_path.stat().st_mtime, tz=UTC)
        # Calculate how long the raw dump has been available since it was last modified.
        dump_age = datetime.now(UTC) - modified_at

        if dump_age < RAW_DUMP_AGE_LIMIT:
            logger.info(
                "Raw database dump not deleted as it had not reached deletion age",
                age_seconds=dump_age.total_seconds(),
                deletion_age=RAW_DUMP_AGE_LIMIT.total_seconds(),
                path=raw_dump_path,
            )
            return

        raw_dump_path.unlink(missing_ok=True)
        logger.info(
            "Deleted raw database dump as it had reached deletion age",
            age_seconds=dump_age.total_seconds(),
            deletion_age=RAW_DUMP_AGE_LIMIT.total_seconds(),
            path=raw_dump_path,
        )
