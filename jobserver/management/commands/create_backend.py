from django.core.management.base import BaseCommand
from django.db import transaction

from jobserver.models import Backend, User


class Command(BaseCommand):
    """
    Create or update a backend

    Designed to be used to automate development setup.
    """

    def add_arguments(self, parser):
        parser.add_argument("slug", default="local-dev", help="The id for backend")
        parser.add_argument("--name", default=None, help="The name will be set to this")
        parser.add_argument(
            "--url", default=None, help="level_4_url will be set to this"
        )
        parser.add_argument(
            "--user", default=None, help="Username to add to the backend"
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="only print the auth token (useful for scripts)",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        backend, created = Backend.objects.get_or_create(
            slug=options["slug"],
            defaults={
                "name": options["name"] or options["slug"],
                "level_4_url": options["url"] or "",
            },
        )
        if created:
            if not options["quiet"]:  # pragma: nocover
                print(f"Created backend {options['name']}")
        else:
            if options["name"]:
                backend.name = options["name"]
            if options["url"]:
                backend.level_4_url = options["url"]
            backend.save()
            if not options["quiet"]:  # pragma: nocover
                print(f"Updated backend {options['name']}")

        if options["user"]:
            user = User.objects.get(username=options["user"])
            if backend not in user.backends.all():
                user.backends.add(backend)
                if not options["quiet"]:  # pragma: nocover
                    print(f"User {options['user']} added to backend")
                user.save()

        print(backend.auth_token)
