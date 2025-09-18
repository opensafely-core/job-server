"""Management command to get a list of RAPs which may need their status checking"""

import structlog
from django.core.management import call_command
from django.core.management.base import BaseCommand

from jobserver.models import JobRequest


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    """Management command to get a list of RAPs which may need their status checking"""

    def handle(self, *args, **options):
        # see model
        completed_states = ["failed", "succeeded", "nothing_to_do"]
        live_job_requests = JobRequest.objects.exclude(status__in=completed_states)
        live_job_request_identifiers = [jr.identifier for jr in live_job_requests]

        if len(live_job_request_identifiers) > 0:
            call_command("rap_status", *live_job_request_identifiers)
        else:
            logger.info("No active RAPs")
