from django.db import transaction
from django_extensions.management.jobs import DailyJob
from sentry_sdk.crons.decorator import monitor

from jobserver.github import _get_github_api
from jobserver.models import Repo
from services.sentry import monitor_config


def topics(data):
    if not data["repositoryTopics"]["nodes"]:
        return []

    return [n["topic"]["name"] for n in data["repositoryTopics"]["nodes"]]


class Job(DailyJob):
    help = "Dump the database to storage for copying to local dev environments"  # noqa: A003

    @monitor(
        monitor_slug="update_repo_has_github_outputs",
        monitor_config=monitor_config("daily"),
    )
    def execute(self):
        query = """
        query reposWithTopics($cursor: String, $org_name: String!) {
          organization(login: $org_name) {
            repositories(first: 100, after: $cursor) {
              nodes {
                url
                repositoryTopics(first: 100) {
                  nodes {
                    topic {
                      name
                    }
                  }
                }
              }
              pageInfo {
                  endCursor
                  hasNextPage
              }
            }
          }
        }
        """
        results = _get_github_api()._iter_query_results(query, org_name="opensafely")
        has_outputs_by_url = {r["url"]: "github-releases" in topics(r) for r in results}

        with transaction.atomic():
            for repo in Repo.objects.all():
                repo.has_github_outputs = has_outputs_by_url.get(repo.url, False)
                repo.save(update_fields=["has_github_outputs"])
