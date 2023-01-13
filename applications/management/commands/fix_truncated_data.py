import csv
import sys

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.models import StudyInformationPage, StudyPurposePage


class Command(BaseCommand):  # pragma: no cover
    def add_arguments(self, parser):
        parser.add_argument("descriptions_path")
        parser.add_argument("purposes_path")

    @transaction.atomic()
    def handle(self, *args, **options):
        with open(options["descriptions_path"]) as f:
            for row in csv.DictReader(f):
                try:
                    page = StudyPurposePage.objects.get(pk=row["id"])
                except StudyPurposePage.DoesNotExist:
                    print(
                        f"StudyPurposePage with ID={row['id']} does not exist",
                        file=sys.stderr,
                    )
                    continue

                page.description = row["description"]
                page.save()

        with open(options["purposes_path"]) as f:
            for row in csv.DictReader(f):
                try:
                    page = StudyInformationPage.objects.get(pk=row["id"])
                except StudyInformationPage.DoesNotExist:
                    print(
                        f"StudyInformationPage with ID={row['id']} does not exist",
                        file=sys.stderr,
                    )
                    continue

                page.study_purpose = row["study_purpose"]
                page.save()
