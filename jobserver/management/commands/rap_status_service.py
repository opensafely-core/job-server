"""Management command to continually update the status of all active Jobs via the RAP API."""

import argparse
import time

import structlog
from django.conf import settings
from django.core.management.base import BaseCommand

from jobserver.commands.rap import get_active_job_request_identifiers, rap_status_update


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to continually update the status of all active Jobs via the RAP API."""

    help = "Update active RAPs' jobs status via the RAP API."

    def add_arguments(self, parser):
        # In production, we want this loop to run forever. Using a
        # function means that we can test it on a finite number of loops.
        parser.add_argument("--run-fn", default=lambda: True, help=argparse.SUPPRESS)

    def handle(self, *args, **options):
        run_fn = options["run_fn"]
        while run_fn():
            try:
                active_job_requests_ids = get_active_job_request_identifiers()
                rap_status_update(active_job_requests_ids)
                time.sleep(settings.RAP_API_POLL_INTERVAL)
            except Exception as exc:
                logger.error(exc)
