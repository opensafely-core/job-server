from urllib.parse import urlparse

import structlog
from django.conf import settings
from django_extensions.management.jobs import YearlyJob


logger = structlog.get_logger(__name__)


class Job(YearlyJob):
    help = "Scrubbed database dump job (in progress)"

    def execute(self):
        readonly_db_url = urlparse(settings.JOBSERVER_READONLY_DATABASE_URL)
        scrubbed_db_url = urlparse(settings.JOBSERVER_SCRUBBED_DATABASE_URL)
        logger.info("Scrubbed database dump job")
        logger.info(
            "Database path for readonly JobServer database",
            database_path=readonly_db_url.path,
        )
        logger.info(
            "Database path for scrubbed JobServer database",
            database_path=scrubbed_db_url.path,
        )
