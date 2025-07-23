import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, *args, **options):
        url = settings.CONTROLLER_API_ENDPOINT

        try:
            response = requests.get(url)

        except requests.exceptions.RequestException:
            raise CommandError("Controller endpoint not available")

        if response.status_code != 200:
            raise CommandError("Controller endpoint returned an error")
