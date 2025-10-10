"""Management command to get the current list of active RAPs / JobRequests."""

import structlog
from django.core.management.base import BaseCommand

from jobserver.commands.rap import get_active_job_request_identifiers


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to get the current list of active RAPs / JobRequests."""

    def handle(self, *args, **options):
        try:
            logger.info(
                "Active job requests", rap_ids=get_active_job_request_identifiers()
            )
        except Exception as exc:
            logger.error(exc)
