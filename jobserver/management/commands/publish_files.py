from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from furl import furl

from jobserver import models, releases


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "username", type=str, help="Username to create the Snapshot with"
        )
        parser.add_argument(
            "workspace", type=str, help="Workspace name to look up files under"
        )
        parser.add_argument(
            "paths", nargs="+", type=str, help="File paths to add to Snapshot"
        )

    def handle(self, *args, **options):
        paths = set(options["paths"])
        username = options["username"]
        workspace = options["workspace"]

        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            raise CommandError(f"Unknown username: {username}")

        try:
            workspace = models.Workspace.objects.get(name=workspace)
        except models.Workspace.DoesNotExist:
            raise CommandError(f"Unknown workspace: {workspace}")

        latest = set(releases.workspace_files(workspace).values())
        requested = [f for f in latest if f.name in paths]

        if missing := paths - {f.name for f in requested}:
            raise CommandError(f"Unknown paths: {', '.join(missing)}")

        publish_request = models.PublishRequest.create_from_files(
            files=requested, user=user
        )

        url = furl(settings.BASE_URL) / publish_request.snapshot.get_absolute_url()
        print(url)
