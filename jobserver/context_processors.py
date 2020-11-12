import functools
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from .models import Job, Stats, Workspace


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def nav(request):
    _active = functools.partial(_is_active, request)

    options = [
        {
            "name": "Workspaces",
            "is_active": _active(reverse("workspace-list")),
            "url": reverse("workspace-list"),
        },
        {
            "name": "Jobs",
            "is_active": _active(reverse("job-list")),
            "url": reverse("job-list"),
        },
    ]

    return {"nav": options}


def site_stats(request):
    acked = Job.objects.filter(started=True).count()
    unacked = Job.objects.exclude(started=True).count()

    try:
        last_seen = Stats.objects.first().api_last_seen
    except AttributeError:
        last_seen = None

    def format_last_seen(last_seen):
        if last_seen is None:
            return "never"

        return last_seen.strftime("%Y-%m-%d %H:%M:%S")

    def show_warning(unacked, last_seen):
        if unacked == 0:
            return False

        if last_seen is None:
            return False

        now = timezone.now()
        five_minutes = timedelta(minutes=5)
        delta = now - last_seen

        if delta < five_minutes:
            return False

        return True

    return {
        "site_stats": {
            "last_seen": format_last_seen(last_seen),
            "queue": {
                "acked": acked,
                "unacked": unacked,
            },
            "show_warning": show_warning(unacked, last_seen),
        }
    }


def workspaces(request):
    return {"workspaces": Workspace.objects.order_by("-created_at")}
