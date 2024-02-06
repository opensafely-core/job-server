import hashlib
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from furl import furl

from jobserver import releases
from jobserver.models import Backend, Project, Repo, User, Workspace


def get_or_maybe_create(create, model, lookup, **kwargs):
    try:
        return model.objects.get(**lookup)
    except model.DoesNotExist:
        if not create:
            raise

        lookup.update(kwargs)
        return model.objects.create(**lookup)


class Command(BaseCommand):
    help = "Release a directory of files to a workspace"  # noqa: A003

    def add_arguments(self, parser):
        parser.add_argument(
            "directory", help="directory of files to release", type=Path
        )
        parser.add_argument(
            "--workspace",
            "-w",
            dest="workspace_name",
            default="test-workspace",
            help="workspace name to release to",
        )
        parser.add_argument(
            "--backend",
            "-b",
            dest="backend_name",
            default="test-backend",
            help="backend to release from",
        )
        parser.add_argument(
            "--user",
            "-u",
            dest="username",
            default="test-user",
            help="user to release with",
        )
        parser.add_argument(
            "--create",
            "-c",
            action="store_true",
            help="create test workspace/backend/user if they do not exist",
        )

    def handle(
        self,
        directory,
        workspace_name,
        backend_name,
        username,
        create,
        *args,
        **options,
    ):
        assert directory.exists()

        files = []

        for filename in directory.glob("**/*"):
            if filename.is_dir():
                continue
            files.append(
                {
                    "name": filename.name,
                    "url": "",
                    "size": filename.stat().st_size,
                    "sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
                    "date": datetime.fromtimestamp(filename.stat().st_mtime, tz=UTC),
                    "metadata": "",
                }
            )
        user = get_or_maybe_create(create, User, {"username": username})

        try:
            workspace = Workspace.objects.get(name=workspace_name)
        except Workspace.DoesNotExist:
            if create:
                project = get_or_maybe_create(
                    create,
                    Project,
                    {"name": "test-project"},
                    slug="test-project",
                    created_by=user,
                    updated_by=user,
                )

                repo = Repo.objects.create(
                    url="https://github.com/opensafely/test-repo"
                )

                workspace = Workspace.objects.create(
                    name=workspace_name,
                    project=project,
                    repo=repo,
                    created_by=user,
                    updated_by=user,
                )
            else:
                raise

        backend = get_or_maybe_create(create, Backend, {"slug": backend_name})

        release = releases.create_release(workspace, backend, user, files)
        for f in files:
            name = f["name"]
            with (directory / name).open("rb") as handle:
                releases.handle_file_upload(release, backend, user, handle, name)

        self.stdout.write("Release created:")
        f = furl(settings.BASE_URL)
        f.path = release.get_absolute_url()
        self.stdout.write(f.url)
        f.path = workspace.get_absolute_url()
        self.stdout.write(f.url)
