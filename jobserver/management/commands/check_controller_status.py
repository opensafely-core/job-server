import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    @staticmethod
    def check_controller_status(url, api_token):
        try:
            response = requests.get(
                f"{url}/backend/status", headers={"Authorization": api_token}
            )

        except requests.exceptions.RequestException:
            raise CommandError("Controller endpoint not available")

        if response.status_code != 200:
            raise CommandError(
                f"Controller endpoint returned an error {response.status_code}"
            )

        return response.content

    def handle(self, *args, **options):
        url = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        logger = structlog.get_logger(__name__)

        try:
            logger.info(self.check_controller_status(url, api_token))
        except CommandError as e:
            logger.error(e)
