"""Management command to update the status of a RAP's Jobs via the RAP API."""

import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api


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
            json_response = rap_api.status(
                options["rap_ids"],
            )

            for job in json_response["jobs"]:
                logger.info(
                    f"RAP: {job['rap_id']} Job: {job['identifier']} Status: {job['status']}"
                )
            for unrecognised_rap_id in json_response["unrecognised_rap_ids"]:
                logger.info(f"Unrecognised RAP id: {unrecognised_rap_id}")

        except Exception as exc:
            logger.error(exc)
