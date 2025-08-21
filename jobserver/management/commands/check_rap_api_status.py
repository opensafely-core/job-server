from urllib.parse import urljoin

import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    @staticmethod
    def check_rap_api_status():
        if not (settings.RAP_API_BASE_URL and settings.RAP_API_TOKEN):
            raise CommandError(
                "Required environment variables RAP_API_BASE_URL and RAP_API_TOKEN are not set"
            )

        try:
            response = requests.get(
                urljoin(settings.RAP_API_BASE_URL, "backend/status/"),
                headers={"Authorization": settings.RAP_API_TOKEN},
            )

        except requests.exceptions.RequestException as e:
            raise CommandError(f"RAP API endpoint not available {e}")

        if response.status_code != 200:
            raise CommandError(
                f"RAP API endpoint returned an error {response.status_code}"
            )

        return response.content

    def handle(self, *args, **options):
        logger = structlog.get_logger(__name__)

        try:
            logger.info(self.check_rap_api_status())
        except CommandError as e:
            logger.error(e)
