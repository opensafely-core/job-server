from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from furl import furl

from jobserver.models import Project
from services.slack import client as slack_client


logger = structlog.get_logger(__name__)


def notify_impending_copilot_windows_closing(days=5):
    """
    Send a message to Slack about an upcoming copilot support windows closing

    This sends a single message to the co-piloting Slack channel to notify of
    Projects whose co-pilot support window ends in the given number of days. If
    there aren't any, it doesn't send a message.

    Each Project found is linked to its Staff Area page.

    Note: URL syntax is using Slack's app surface linking syntax, which is
    different from the markdown syntax:

        https://api.slack.com/reference/surfaces/formatting#linking-urls

    """
    if settings.DEBUG:
        return

    start_date = timezone.now()
    end_date = start_date + timedelta(days=days)
    projects = Project.objects.filter(
        copilot_support_ends_at__range=(start_date, end_date)
    ).order_by("copilot_support_ends_at")

    if not projects:
        logger.info(
            "No projects with copilot support windows closing within %s days" % days
        )
        return

    def build_line(p):
        f = furl(settings.BASE_URL)
        f.path = p.get_staff_url()

        end_date = naturalday(p.copilot_support_ends_at)

        return f"\n * <{f.url}|{p.name}> ({end_date})"

    project_urls = [build_line(p) for p in projects]
    message = f"Projects with support window ending soon:{''.join(project_urls)}"

    slack_client.chat_postMessage(
        channel="co-pilot-support",
        text=message,
    )
