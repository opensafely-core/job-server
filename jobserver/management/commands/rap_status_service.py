"""Management command to continually update the status of all active Jobs via the RAP API."""

import time

import structlog
from django.core.management.base import BaseCommand

from jobserver.commands.rap import get_active_job_request_ids, rap_status_update


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to continually update the status of all active Jobs via the RAP API."""

    help = "Update active RAPs' jobs status via the RAP API."

    def handle(self, *args, **options):
        try:
            while True:
                active_job_requests_ids = get_active_job_request_ids()
                rap_status_update(active_job_requests_ids)
                time.sleep(60)
        except Exception as exc:
            logger.error(exc)
