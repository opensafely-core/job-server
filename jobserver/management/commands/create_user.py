from django.core.management.base import BaseCommand
from django.db import transaction

from jobserver.authorization.roles import (
    CoreDeveloper,
    OutputChecker,
)
from jobserver.models import get_or_create_user


class Command(BaseCommand):
    """
    Create or update a workspace.

    Will create Project and Repo as needed, and ensure the supplied user as
    Project Developer of the workspace.
    """

    def add_arguments(self, parser):
        parser.add_argument("username", help="User to create")
        parser.add_argument("--email", help="Defaults to username@example.com")
        parser.add_argument("--name", help="Defaults to username")
        parser.add_argument(
            "--output-checker",
            action="store_true",
            help="Make user global OutputChecker",
        )
        parser.add_argument(
            "--core-developer",
            action="store_true",
            help="Make user global CoreDeveloper",
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        username = options["username"]

        update_fields = []
        if options["email"]:
            update_fields.append("email")
        if options["name"]:
            update_fields.append("fullname")

        user, created = get_or_create_user(
            username,
            email=options["email"] or f"{username}@example.com",
            fullname=options["name"] or username,
            update_fields=update_fields,
        )
        print(f"User {username} {'created' if created else 'updated'}")

        roles = []
        if options["output_checker"]:
            roles.append(OutputChecker)
        if options["core_developer"]:
            roles.append(CoreDeveloper)

        updated = False
        for role in roles:
            if role not in user.roles:
                updated = True
                print(f"Added {role.__name__} global role to user {user.username}")
                user.roles.append(role)
            else:
                print(f"User {user.username} already has role {role.__name__}")

        if updated:
            user.save()
