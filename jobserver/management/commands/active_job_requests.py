"""Management command to get the current list of active RAPs / JobRequests."""

import structlog
from django.core.management.base import BaseCommand

from jobserver.commands.rap import get_active_job_request_ids


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to get the current list of active RAPs / JobRequests."""

    def handle(self, *args, **options):
        try:
            logger.info(get_active_job_request_ids())
        except Exception as exc:
            logger.error(exc)
