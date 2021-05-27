import csv

from django.core.management.base import BaseCommand
from django.db import transaction
from environs import Env

from ...models import Org, OrgMembership, User


env = Env()

MAPPINGS_PATH = env.str("MAPPINGS_PATH")


class Command(BaseCommand):
    @transaction.atomic()
    def handle(self, *args, **options):
        with open(MAPPINGS_PATH) as f:
            mappings = list(csv.DictReader(f))

        for row in mappings:
            org = Org.objects.get(slug=row["org_slug"])

            for username in row["usernames"].split(","):
                user = User.objects.get(username=username)
                OrgMembership.objects.create(org=org, user=user)
                print(f"Assigned '{org.slug}' <> '{username}'")
