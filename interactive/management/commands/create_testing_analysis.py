import hashlib
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from furl import furl

from interactive.commands import create_report
from interactive.models import AnalysisRequest
from jobserver.models import Backend, JobRequest, Project, Release, ReleaseFile, User
from jobserver.models.core import new_id


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "creator", help="Username to use for the creator of various objects"
        )

    @transaction.atomic()
    def handle(self, *args, creator, **options):
        try:
            user = User.objects.get(username=creator)
        except User.DoesNotExist:
            self.stderr.write(f'No user with username "{creator}" found.')
            sys.exit(1)

        backend = Backend.objects.get(slug="test")
        project = Project.objects.get(slug="opensafely-internal")

        job_request = JobRequest.objects.create(
            created_by=user,
            backend=backend,
            workspace=project.interactive_workspace,
            requested_actions=["testing"],
        )

        # create a successful job so the analysis can be successful
        job_request.jobs.create(
            action="testing",
            identifier=new_id(),
            status="succeeded",
        )

        analysis_request = AnalysisRequest.objects.create(
            created_by=user,
            job_request=job_request,
            project=project,
            updated_by=user,
            title="Testing Analysis",
            report_title="Testing Report",
        )

        # create a release so we have a place to put the file
        release = Release.objects.create(
            created_by=user,
            workspace=project.interactive_workspace,
        )

        # build up some paths:

        # the directory name for use in the name field on our ReleaseFile
        name = Path(
            "output",
            analysis_request.pk,
        )
        # the directory without our configured releases one so we can use it to
        # set the path field on the ReleaseFile
        directory = Path(project.interactive_workspace.name, release.pk) / name

        # an absolute path to the directory so we can create it
        absolute_directory = settings.RELEASE_STORAGE / directory
        absolute_directory.mkdir(parents=True)

        # an absolute path to the file
        file_path = absolute_directory / "report.html"

        # copy the file to the release directory
        shutil.copyfile("outputs/interactive_testing_report.html", file_path)

        # Create a release for the file
        stat = os.stat(file_path)
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        rfile = ReleaseFile.objects.create(
            created_by=user,
            workspace=project.interactive_workspace,
            uploaded_at=timezone.now(),
            path=directory / "report.html",
            name=name / "report.html",
            filehash=hashlib.sha256(file_path.read_bytes()).hexdigest(),
            mtime=mtime,
            size=stat.st_size,
        )

        release.files.add(rfile)

        create_report(
            analysis_request=analysis_request,
            rfile=rfile,
            user=analysis_request.created_by,
        )

        f = furl(settings.BASE_URL)
        f.path = analysis_request.get_absolute_url()
        print(f)
