import sys
from pathlib import Path

from django.core.management.base import BaseCommand

from jobserver.models import Backend, Workspace
from jobserver.releases import create_upload_zip, handle_release


class Command(BaseCommand):
    help = "Release a directory of files to a workspace"

    def add_arguments(self, parser):
        parser.add_argument("workspace_name", help="worksapace name to release to")
        parser.add_argument("backend_name", help="backend to release from")
        parser.add_argument("directory", help="directory of files to release")

    def handle(self, workspace_name, backend_name, directory, *args, **options):
        try:
            workspace = Workspace.objects.get(name=workspace_name)
            backend = Backend.objects.get(name=backend_name)
            release_hash, zipstream = create_upload_zip(Path(directory))
            handle_release(workspace, backend, "local user", release_hash, zipstream)
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
