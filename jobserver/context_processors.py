import functools

from django.urls import reverse

from .backends import show_warning
from .models import JobRequest, Stats


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def backend_warnings(request):
    try:
        last_seen = Stats.objects.first().api_last_seen
    except AttributeError:
        last_seen = None

    unacked = JobRequest.objects.unacked().count()
    if not show_warning(unacked, last_seen):
        return {"backend_warnings": []}

    return {"backend_warnings": ["TPP"]}


def nav(request):
    _active = functools.partial(_is_active, request)

    options = [
        {
            "name": "Event Log",
            "is_active": _active(reverse("job-list")),
            "url": reverse("job-list"),
        },
        {
            "name": "Status",
            "is_active": _active(reverse("status")),
            "url": reverse("status"),
        },
    ]

    return {"nav": options}
