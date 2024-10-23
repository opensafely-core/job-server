from django.core.management.base import BaseCommand
from django.db import transaction

from jobserver.authorization.roles import (
    OutputChecker,
    StaffAreaAdministrator,
)
from jobserver.models import User


class Command(BaseCommand):
    """Create or update a User."""

    help = "Create or update a User"

    def add_arguments(self, parser):
        parser.add_argument("username", help="User to create or update")
        parser.add_argument("--email", help="Defaults to username@example.com")
        parser.add_argument("--name", help="Defaults to username")
        parser.add_argument(
            "-o",
            "--output-checker",
            action="store_true",
            help="Make user global OutputChecker",
        )
        parser.add_argument(
            "-s",
            "--staff-area-administrator",
            action="store_true",
            help="Make user global StaffAreaAdministrator",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        username = options["username"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": options["email"] or f"{username}@example.com",
                "fullname": options["name"] or username,
            },
        )
        self.stdout.write(f"User {username} {'created' if created else 'updated'}")

        roles = []
        if options["output_checker"]:
            roles.append(OutputChecker)
        if options["staff_area_administrator"]:
            roles.append(StaffAreaAdministrator)

        updated = False
        for role in roles:
            if role not in user.roles:
                updated = True
                self.stdout.write(
                    f"Added {role.__name__} global role to user {user.username}"
                )
                user.roles.append(role)
            else:
                self.stdout.write(
                    f"User {user.username} already has role {role.__name__}"
                )

        if updated:
            user.save()
