import structlog
from django.core.management.base import BaseCommand

from jobserver import rap_api


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger = structlog.get_logger(__name__)

        try:
            logger.info(rap_api.backend_status())
        except Exception as exc:
            logger.error(exc)
