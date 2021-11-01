import sys

from django.core.management.base import BaseCommand

from jobserver.backends import ensure_backends


class Command(BaseCommand):
    help = "Ensure backends are configured"  # noqa: A003

    def handle(self, *args, **options):
        try:
            ensure_backends()
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
