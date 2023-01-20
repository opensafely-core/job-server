import hashlib
import shutil
import sys
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from interactive.dates import END_DATE, START_DATE
from interactive.models import AnalysisRequest
from jobserver.models import Backend, User, Workspace


BASE_URL = f"{settings.BASE_URL}/api/v2/releases/"


def create_file(*, new_path):
    report_path = settings.BASE_DIR / "outputs/interactive_report.html"
    shutil.copy(report_path, new_path)


def create_release(*, backend, path, user):
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
    url = f"{BASE_URL}workspace/opensafely-internal-interactive"
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()

    return r.json()["release_id"]


def submit_request(*, backend, user, workspace):
    # create a JobRequest and AnalysisRequest to mirror a user making a request
    job_request = workspace.job_requests.create(
        backend=backend,
        created_by=user,
        sha="",
        project_definition="",
        force_run_dependencies=True,
        requested_actions=["run_all"],
    )

    return AnalysisRequest.objects.create(
        job_request=job_request,
        project=workspace.project,
        created_by=user,
        title="get from form",
        start_date=START_DATE,
        end_date=END_DATE,
        codelist_slug="get from form",
        codelist_name="get from form",
    )


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
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        try:
            me = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"No user found with username: '{username}'")
            )
            sys.exit(1)

        tpp = Backend.objects.get(slug="tpp")
        internal = Workspace.objects.get(name="opensafely-internal-interactive")

        # create a file with the pk of the AR
        analysis_request = submit_request(backend=tpp, user=me, workspace=internal)

        # set up the path we're going to use to upload the file from
        tmp_path = settings.BASE_DIR / f"{analysis_request.pk}.html"

        try:
            create_file(new_path=tmp_path)
            release_id = create_release(backend=tpp, path=tmp_path, user=me)
            upload_file(backend=tpp, release_id=release_id, path=tmp_path, user=me)
        finally:
            tmp_path.unlink()

        print(f"{settings.BASE_URL}{analysis_request.get_absolute_url()}")
