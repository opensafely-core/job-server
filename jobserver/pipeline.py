from django.conf import settings
from furl import furl

from services.slack import client as slack_client


def notify_on_new_user(user, is_new, *args, **kwargs):
    if not is_new:
        return

    f = furl(settings.BASE_URL)
    f.path = user.get_staff_url()

    slack_client.chat_postMessage(
        channel="job-server-registrations",
        text=f"New user ({user.username}) registered: {f.url}",
    )


def set_notifications_email(user, *args, **kwargs):
    """
    Set a User's notifications_email if it's not already set

    When a User first signs up to the service they don't have their
    notifications_email set, so we copy the value passed to us from GitHub to
    that value.
    """
    if not user.notifications_email:
        user.notifications_email = user.email
        user.save()
