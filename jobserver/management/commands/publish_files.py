from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from furl import furl

from jobserver import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument(
            "ids", nargs="+", type=str, help="ReleaseFile IDs to add to Snapshot"
        )

    def handle(self, *args, **options):
        ids = set(options["ids"])
        username = options["username"]

        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            raise CommandError(f"Unknown username: {username}")

        rfiles = models.ReleaseFile.objects.filter(pk__in=ids)

        found = set(rfiles.values_list("pk", flat=True))
        if unknown := ids - found:
            raise CommandError(f"Unknown ReleaseFiles: {', '.join(unknown)}")

        publish_request = models.PublishRequest.create_from_files(
            files=rfiles, user=user
        )

        url = furl(settings.BASE_URL) / publish_request.snapshot.get_absolute_url()
        print(url)
