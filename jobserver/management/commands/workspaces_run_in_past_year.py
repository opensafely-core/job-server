import json
import re
from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from ...models import JobRequest, Workspace


class Command(BaseCommand):
    def handle(self, *args, **options):
        one_year_ago = datetime.now(tz=UTC) - timedelta(days=365)
        workspace_ids_run_in_past_year = set(
            JobRequest.objects.filter(
                backend__slug="tpp", created_at__gte=one_year_ago
            ).values_list("workspace", flat=True)
        )
        workspaces = Workspace.objects.filter(id__in=workspace_ids_run_in_past_year)

        workspace_data = {
            repo_full_name(workspace.repo.url): {
                "name": workspace.name,
                "project": workspace.project.name,
                "url": f"https://jobs.opensafely.org{workspace.get_absolute_url()}",
                "repo": workspace.repo.url,
                "branch": workspace.branch,
            }
            for workspace in workspaces
        }

        outfile = settings.BASE_DIR / "workspaces_run_in_past_year.json"
        outfile.write_text(json.dumps(workspace_data, indent=2))


def repo_full_name(repo_url):
    match = re.match(r".+(opensafely/.+)/?$", repo_url)
    return match.groups()[0]
