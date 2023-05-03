import hashlib
import sys
from datetime import UTC, datetime

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from interactive.models import AnalysisRequest
from jobserver.models import Backend, User


BASE_URL = f"{settings.BASE_URL}/api/v2/releases/"


def create_release(*, backend, local_file, release_filename, workspace_name, user):
    headers = {
        "Authorization": backend.auth_token,
        "Content-Type": "application/json",
        "OS-User": user.username,
    }
    payload = {
        "files": [
            {
                "name": release_filename,
                "url": "http://localhost:8001",
                "size": local_file.stat().st_size,
                "sha256": hashlib.sha256(local_file.read_bytes()).hexdigest(),
                "date": datetime.fromtimestamp(
                    local_file.stat().st_mtime, tz=UTC
                ).isoformat(),
                "metadata": {},
                "review": {
                    "status": "APPROVED",
                    "comments": {},
                },
            }
        ],
        "metadata": {},
        "review": {},
    }
    url = f"{BASE_URL}workspace/{workspace_name}"
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()

    return r.json()["release_id"]


def upload_file(*, backend, release_id, local_file, release_filename, user):
    headers = {
        "Authorization": backend.auth_token,
        "Content-Disposition": f'attachment; filename="{release_filename}"',
        "Content-Type": "application/octet-stream",
        "OS-User": user.username,
    }
    url = f"{BASE_URL}release/{release_id}"
    r = requests.post(url, data=local_file.read_bytes(), headers=headers)
    r.raise_for_status()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_request_slug",
            help="Analysis request slug to link the released file to",
        )
        parser.add_argument("username", help="User to release the file under")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.filter(username=username).first()
        if user is None:
            self.stderr.write(
                self.style.ERROR(f"No user found with username: '{username}'")
            )
            sys.exit(1)

        slug = options["analysis_request_slug"]
        analysis_request = AnalysisRequest.objects.filter(slug=slug).first()
        if analysis_request is None:
            self.stderr.write(self.style.ERROR(f"Unknown Analysis: {slug}"))
            sys.exit(1)

        tpp = Backend.objects.get(slug="tpp")

        release_filename = f"output/{analysis_request.pk}/report.html"
        local_file = (
            settings.BASE_DIR / "workspaces" / analysis_request.pk / "report.html"
        )

        release_id = create_release(
            backend=tpp,
            local_file=local_file,
            release_filename=release_filename,
            workspace_name=analysis_request.project.interactive_workspace.name,
            user=user,
        )
        upload_file(
            backend=tpp,
            release_id=release_id,
            local_file=local_file,
            release_filename=release_filename,
            user=user,
        )

        print(f"{settings.BASE_URL}{analysis_request.get_absolute_url()}")
