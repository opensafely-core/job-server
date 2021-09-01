from services.slack import client as slack_client


def slack(event):
    channel = event.slack_channel if hasattr(event, "slack_channel") else "tech"

    slack_client.chat_postMessage(channel=channel, text=str(event))
