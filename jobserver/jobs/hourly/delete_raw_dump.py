"""
Hourly job to delete raw JobServer database dumps after their retention period.

Raw database dumps may contain production personal data and other sensitive
information. They are created manually using the dump_raw_data management
command when access has been agreed and recorded in accordance with the
Personal Data Copying Policy.

The raw dump needs to remain available for long enough for an authorised
developer to download it, but it should not remain on the production server
indefinitely. This job limits that exposure by deleting the dump once it has
existed for at least one hour.

The age of the dump is determined from its modification time. Checking its age,
rather than deleting any dump that exists, prevents a newly created dump from
being deleted by an hourly run before it can be downloaded.

Because this job runs once an hour, a dump will normally be deleted between one
and two hours after it is created. A missing dump is expected and is not treated
as an error.
"""

from datetime import UTC, datetime, timedelta

import structlog
from django.conf import settings
from django_extensions.management.jobs import HourlyJob, JobError
from sentry_sdk.crons.decorator import monitor

from services.sentry import monitor_config


logger = structlog.get_logger(__name__)

RAW_DUMP_RETENTION_PERIOD = timedelta(hours=1)
"""Minimum period for which a raw dump remains available before deletion."""


class Job(HourlyJob):
    help = "Delete raw database dumps after the retention period to limit the availability of production data"

    @monitor(monitor_slug="delete_raw_dump", monitor_config=monitor_config("0 * * * *"))
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

        if dump_age < RAW_DUMP_RETENTION_PERIOD:
            logger.info(
                "Raw database dump is still within its retention period",
                age_seconds=dump_age.total_seconds(),
                path=raw_dump_path,
            )
            return

        raw_dump_path.unlink(missing_ok=True)
        logger.info(
            "Deleted raw database dump after its retention period",
            age_seconds=dump_age.total_seconds(),
            path=raw_dump_path,
        )
