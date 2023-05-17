from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_request_slug",
            help="Analysis request slug to link the released file to",
        )
        parser.add_argument("username", help="User to release the file under")

    def handle(self, *args, **options):
        analysis_request_pk = options["analysis_request_slug"].split("-")[-1]
        report = Path(f"workspaces/{analysis_request_pk}/report.html")
        call_command("osi_run", options["analysis_request_slug"])
        call_command(
            "osi_release",
            options["analysis_request_slug"],
            options["username"],
            report=report,
        )
