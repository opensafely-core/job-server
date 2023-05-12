import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand
from interactive_templates import git

from interactive.models import AnalysisRequest


def copy_report(*, from_path, analysis_request):
    report_path = Path(from_path) / "output" / analysis_request.pk / "report.html"
    new_path = Path("workspaces") / analysis_request.pk / "report.html"
    new_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(report_path, new_path)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_request_slug",
            help="Analysis request slug to link the released file to",
        )

    def handle(self, *args, **options):
        slug = options["analysis_request_slug"]
        analysis_request = AnalysisRequest.objects.filter(slug=slug).first()
        if analysis_request is None:
            self.stderr.write(self.style.ERROR(f"Unknown Analysis: {slug}"))
            sys.exit(1)

        repo = analysis_request.project.interactive_workspace.repo

        with tempfile.TemporaryDirectory(suffix=f"repo-{analysis_request.pk}") as path:
            git("clone", repo.url, path)

            cmd = [
                "opensafely",
                "run",
                "run_all",
                "--project-dir",
                path,
                "--timestamps",
            ]

            self.stdout.write(f"Executing: {' '.join(cmd)}")

            subprocess.run(cmd, check=True)

            copy_report(from_path=path, analysis_request=analysis_request)
