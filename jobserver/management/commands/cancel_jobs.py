"""Management command to cancel Jobs via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to cancel Jobs via the RAP API."""

    help = "Cancel RAP jobs via the RAP API."

    def add_arguments(self, parser):
        parser.add_argument(
            "rap_id",
            type=str,
            help="ID of the RAP to cancel. Equivalent to JobRequest.identifier.",
        )
        parser.add_argument(
            "actions",
            nargs="+",
            type=str,
            help="List of actions to cancel for the given RAP.",
        )

    def handle(self, *args, **options):
        try:
            logger.info(
                rap_api.cancel(
                    options["rap_id"],
                    options["actions"],
                )
            )
        except Exception as exc:
            logger.error(exc)
