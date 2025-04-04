import sys

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from ...models import User


class Command(BaseCommand):
    help = "Create a bot user and print its token"  # noqa: A003

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        fullname = username.replace("-", " ").title()

        try:
            user = User.objects.create(username=username, fullname=fullname)
        except IntegrityError:
            sys.exit(f"User '{username}' already exists")

        token = user.rotate_token()

        print(f"New token: {user.username}:{token}")
