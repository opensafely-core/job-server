from services import slack

from .config import ORG_SLACK_CHANNELS


def post_slack_update(org, update_url, issue_title, update_text):
    channel = ORG_SLACK_CHANNELS.get(org, ORG_SLACK_CHANNELS["default"])

    title_link = slack.link(update_url, f"{issue_title} has been updated")
    message_text = f"{title_link}\n{update_text}"
    slack.post(message_text, channel)
