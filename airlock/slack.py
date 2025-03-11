from services import slack

from .config import ORG_SLACK_CHANNELS


def post_slack_update(org, update_url, issue_title, update_text, github_error):
    channel = ORG_SLACK_CHANNELS.get(org, ORG_SLACK_CHANNELS["default"])

    if update_url is not None:
        title = slack.link(update_url, f"{issue_title} has been updated")
    else:
        title = f"{issue_title} has been updated"
    message_text = f"{title}\n{update_text}"

    if github_error:
        message_text += f"\nA GitHub error occurred: {github_error}"

    slack.post(message_text, channel)
