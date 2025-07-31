from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from furl import furl

from jobserver.models import ReleaseFile, Snapshot


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "snapshot", type=str, help="ID of Snapshot from which to remove files"
        )
        parser.add_argument(
            "paths", nargs="+", type=str, help="File paths to remove from Snapshot"
        )

    @transaction.atomic()
    def handle(self, *args, **options):
        snapshot_id = options["snapshot"]
        try:
            snapshot = Snapshot.objects.get(id=snapshot_id)
        except Snapshot.DoesNotExist:
            raise CommandError(f"Unknown snapshot: {snapshot_id}")

        if snapshot.is_published:
            raise CommandError(
                f"Snapshot {snapshot_id} has been published and cannot be edited"
            )

        paths = set(options["paths"])
        release_files = []
        for path in paths:
            try:
                release_file = ReleaseFile.objects.filter(
                    workspace=snapshot.workspace
                ).get(name=path)
                release_files.append(release_file)
            except ReleaseFile.DoesNotExist:
                raise CommandError(f"Unknown file path: {path}")

        for release_file in release_files:
            snapshot.files.remove(release_file)

        url = furl(settings.BASE_URL) / snapshot.get_absolute_url()
        self.stdout.write(f"{len(release_files)} files removed from {url}")
