from datetime import timedelta

import structlog
from django.utils import timezone

from jobserver.models import Project
from jobserver.slacks import notify_copilot_windows_closing


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
    start_date = timezone.now()
    end_date = start_date + timedelta(days=days)
    projects = Project.objects.filter(
        copilot_support_ends_at__range=(start_date, end_date)
    ).order_by("copilot_support_ends_at")

    if not projects:
        logger.info(
            f"No projects with copilot support windows closing within {days} days"
        )
        return

    notify_copilot_windows_closing(projects)
