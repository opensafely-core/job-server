"""Management command to update the status of a RAP's Jobs via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver.actions.rap import rap_status_update


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to update the status of a RAP's Jobs via the RAP API."""

    help = "Update RAP's jobs status via the RAP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "rap_ids",
            nargs="+",
            type=str,
            help="IDs of the RAPs to update.",
        )

    def handle(self, *args, **options):
        try:
            rap_status_update(options["rap_ids"])
        except Exception as exc:
            logger.error(exc)
