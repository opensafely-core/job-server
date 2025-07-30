import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    @staticmethod
    def check_controller_status(url):
        try:
            response = requests.get(url)

        except requests.exceptions.RequestException:
            raise CommandError("Controller endpoint not available")

        if response.status_code != 200:
            raise CommandError("Controller endpoint returned an error")

        return response.content

    def handle(self, *args, **options):
        url = settings.RAP_API_ENDPOINT

        print(self.check_controller_status(url))
