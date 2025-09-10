import datetime

import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api
from jobserver.models import Stats


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger = structlog.get_logger(__name__)

        try:
            logger.info(rap_api.backend_status())
        except Exception as exc:
            logger.error(exc)

    def update_backend_state(backend, request):
        # Retrieve the response gotten from the jobrunner endpoint
        flags = rap_api.backend_status().get("backends", [])

        if not flags:
            return

        jobrunner_state = flags[0]

        # Record the time we're told this backend was last seen alive, for availability
        # reporting purposes
        if last_seen_at_flag := jobrunner_state.get("last_seen"):
            last_seen_at_dt = datetime.datetime.fromisoformat(last_seen_at_flag)
            Stats.objects.update_or_create(
                backend=backend,
                url=request.path,
                defaults={"api_last_seen": last_seen_at_dt},
            )

        backend.rap_api_state = jobrunner_state
        backend.save(update_fields=["rap_api_state"])
