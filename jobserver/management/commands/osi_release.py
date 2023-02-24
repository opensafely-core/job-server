import hashlib
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from interactive.models import AnalysisRequest
from jobserver.models import Backend, User


BASE_URL = f"{settings.BASE_URL}/api/v2/releases/"


def create_file(*, new_path):
    report_path = settings.BASE_DIR / "outputs/interactive_report.html"
    shutil.copy(report_path, new_path)


def create_release(*, backend, path, workspace_name, user):
    headers = {
        "Authorization": backend.auth_token,
        "Content-Type": "application/json",
        "OS-User": user.username,
    }
    payload = {
        "files": [
            {
                "name": path.name,
                "url": "http://localhost:8001",
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "date": datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
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


def upload_file(*, backend, release_id, path, user):
    headers = {
        "Authorization": backend.auth_token,
        "Content-Disposition": f'attachment; filename="{path.name}"',
        "Content-Type": "application/octet-stream",
        "OS-User": user.username,
    }
    url = f"{BASE_URL}release/{release_id}"
    r = requests.post(url, data=path.read_bytes(), headers=headers)
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

        with tempfile.TemporaryDirectory(suffix=f"output-{analysis_request.pk}") as tmp:
            # set up the path we're going to use to upload the file from
            tmp_path = Path(tmp) / f"{analysis_request.pk}.html"

            try:
                create_file(new_path=tmp_path)
                release_id = create_release(
                    backend=tpp,
                    path=tmp_path,
                    workspace_name=analysis_request.project.interactive_workspace.name,
                    user=user,
                )
                upload_file(
                    backend=tpp, release_id=release_id, path=tmp_path, user=user
                )
            finally:
                tmp_path.unlink()
        print(f"{settings.BASE_URL}{analysis_request.get_absolute_url()}")
