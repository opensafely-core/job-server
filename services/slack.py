import os

import structlog
from django.conf import settings
from furl import furl
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = structlog.get_logger(__name__)

slack_token = os.environ.get("SLACK_BOT_TOKEN", default="")

client = WebClient(token=slack_token)


def post(text, channel):
    if settings.DEBUG:  # pragma: no cover
        print("")
        print(f"Channel: {channel}")
        print("Message:")
        print(text)
        print("")
        return

    try:
        client.chat_postMessage(channel=channel, text=text)
    except SlackApiError:
        # failing to slack is never fatal, so log and do not error
        logger.exception(
            f"Failed to notify slack in channel: {channel}", channel=channel
        )


def link(url, text=None):
    """Because no one can remember this shit."""
    if url.startswith("/"):
        base_url = furl(settings.BASE_URL)
        base_url.path = url
        url = base_url.url

    if text is None:
        return f"<{url}>"
    else:
        return f"<{url}|{text}>"
