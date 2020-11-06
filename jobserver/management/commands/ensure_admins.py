import sys

from django.core.management.base import BaseCommand

from jobserver.admins import ensure_admins, get_admins


class Command(BaseCommand):
    help = "Configure admins to "

    def handle(self, *args, **options):
        usernames = get_admins()

        try:
            ensure_admins(usernames)
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
