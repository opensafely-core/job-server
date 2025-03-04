"""
Functions for specific slack messages jobserver sends.

These functions should always take a `channel` argument, so that we can test
them on a different channel.
"""

from jobserver.utils import strip_whitespace
from services import slack


def notify_report_uploaded(analysis_request, channel="interactive-requests"):
    analysis_url = slack.link(analysis_request.get_absolute_url(), "View on job-server")

    message = f"""
    *Report uploaded*
    Title: {analysis_request.report_title}

    {analysis_url}
    """

    message = strip_whitespace(message)

    slack.post(message, channel)
