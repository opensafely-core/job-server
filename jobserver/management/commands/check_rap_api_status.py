from datetime import datetime

import structlog
from django.conf import settings
from django.core.management.base import BaseCommand

from jobserver import rap_api
from jobserver.models import Backend, Stats


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger = structlog.get_logger(__name__)

        try:
            # Retrieve the response gotten from the rap_api endpoint
            backend_status_response = rap_api.backend_status()
            backends = backend_status_response["backends"]

            for backend_states in backends:
                backend_name = backend_states["name"]

                backend_object = Backend.objects.get(name=backend_name)

                # Record the time we're told this backend was last seen alive, for availability
                # reporting purposes
                last_seen_at = backend_states["last_seen"]
                if not last_seen_at:
                    backend_object.last_seen_at = None
                else:
                    last_seen_at_dt = datetime.fromisoformat(last_seen_at)
                    Stats.objects.update_or_create(
                        backend=backend_object,
                        url=settings.RAP_API_BASE_URL,
                        defaults={"api_last_seen": last_seen_at_dt},
                    )
                    backend_object.last_seen_at = last_seen_at_dt

                # Record the time this backend was last in maintenance mode
                last_seen_in_maintenance_mode = backend_states["db_maintenance"][
                    "since"
                ]
                if not last_seen_in_maintenance_mode:
                    backend_object.last_seen_maintenance_mode = None

                else:
                    last_seen_dt_maintenance_mode = datetime.fromisoformat(
                        last_seen_in_maintenance_mode
                    )
                    backend_object.last_seen_maintenance_mode = (
                        last_seen_dt_maintenance_mode
                    )

                backend_object.rap_api_state = backend_states

                backend_object.save(
                    update_fields=[
                        "rap_api_state",
                        "last_seen_at",
                        "last_seen_maintenance_mode",
                    ]
                )
            logger.info(backend_status_response)

        except Exception as exc:
            logger.error(exc)
