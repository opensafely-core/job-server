from django.conf import settings
from furl import furl
from incuna_mail import send

from jobserver.models import Release


def get_email_context(airlock_event):
    # The first update is the event itself, don't include this in emails
    updates = airlock_event.describe_updates()[1:]
    return {
        "release_request_id": airlock_event.release_request_id,
        "request_author": airlock_event.request_author.name,
        "workspace": airlock_event.workspace.name,
        "updates": updates,
    }


def send_request_released_email(airlock_event):
    release = Release.objects.get(id=airlock_event.release_request_id)
    f = furl(settings.BASE_URL)
    f.path = release.get_absolute_url()

    context = get_email_context(airlock_event)
    context["url"] = f.url

    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Files released for workspace {airlock_event.workspace.name}",
        template_name="airlock/emails/request_released.txt",
        html_template_name="airlock/emails/request_released.html",
        context=context,
    )


def send_request_rejected_email(airlock_event):
    context = get_email_context(airlock_event)
    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Release request rejected: {airlock_event.workspace.name} ({airlock_event.release_request_id})",
        template_name="airlock/emails/request_rejected.txt",
        html_template_name="airlock/emails/request_rejected.html",
        context=context,
    )


def send_request_returned_email(airlock_event):
    context = get_email_context(airlock_event)
    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Release request returned: {airlock_event.workspace.name} ({airlock_event.release_request_id})",
        template_name="airlock/emails/request_returned.txt",
        html_template_name="airlock/emails/request_returned.html",
        context=context,
    )
