from django.core.management.base import BaseCommand

from interactive.models import AnalysisRequest
from interactive.submit import resubmit_analysis
from jobserver.github import _get_github_api


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_request_slug",
            help="Analysis request slug/id to resubmit",
        )

    def handle(self, analysis_request_slug, *args, **options):
        analysis_request = AnalysisRequest.objects.get(pk=analysis_request_slug)
        resubmit_analysis(analysis_request, _get_github_api)
        print(f"New job request: {analysis_request.job_request.get_absolute_url()}")
