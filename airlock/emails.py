from django.conf import settings
from furl import furl
from incuna_mail import send

from jobserver.models import Release


def send_request_released_email(airlock_event):
    release = Release.objects.get(id=airlock_event.release_request_id)
    f = furl(settings.BASE_URL)
    f.path = release.get_absolute_url()

    context = {
        "url": f.url,
        "request_author": airlock_event.request_author.name,
        "workspace": airlock_event.workspace.name,
    }

    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Files released for workspace {airlock_event.workspace.name}",
        template_name="airlock/emails/request_released.txt",
        html_template_name="airlock/emails/request_released.html",
        context=context,
    )


def send_request_rejected_email(airlock_event):
    context = {
        "release_request_id": airlock_event.release_request_id,
        "request_author": airlock_event.request_author.name,
        "workspace": airlock_event.workspace.name,
    }

    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Release request rejected: {airlock_event.workspace.name} ({airlock_event.release_request_id})",
        template_name="airlock/emails/request_rejected.txt",
        html_template_name="airlock/emails/request_rejected.html",
        context=context,
    )


def send_request_updated_email(airlock_event):
    context = {
        "release_request_id": airlock_event.release_request_id,
        "request_author": airlock_event.request_author.name,
        "workspace": airlock_event.workspace.name,
        # Currently there is only one update event at a time; the template
        # takes a list of update strings to allow for sending a batch of
        # updates at once
        "updates": [airlock_event.describe_update()],
    }

    send(
        to=airlock_event.request_author.email,
        sender="notifications@jobs.opensafely.org",
        subject=f"Release request updated: {airlock_event.workspace.name} ({airlock_event.release_request_id})",
        template_name="airlock/emails/request_updated.txt",
        html_template_name="airlock/emails/request_updated.html",
        context=context,
    )
