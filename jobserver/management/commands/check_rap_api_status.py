import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    @staticmethod
    def check_rap_api_status(endpoint, api_token):
        try:
            response = requests.get(
                f"{endpoint}/backend/status", headers={"Authorization": api_token}
            )

        except requests.exceptions.RequestException as e:
            raise CommandError(f"RAP API endpoint not available {e}")

        if response.status_code != 200:
            raise CommandError(
                f"RAP API endpoint returned an error {response.status_code}"
            )

        return response.content

    def handle(self, *args, **options):
        endpoint = settings.RAP_API_ENDPOINT
        api_token = settings.RAP_API_TOKEN

        logger = structlog.get_logger(__name__)

        try:
            logger.info(self.check_rap_api_status(endpoint, api_token))
        except CommandError as e:
            logger.error(e)
