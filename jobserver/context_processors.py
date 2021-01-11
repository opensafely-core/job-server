import functools

from django.urls import reverse

from .backends import show_warning
from .models import Backend, Stats


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def backend_warnings(request):
    def iter_warnings(backends):
        for backend in backends:
            try:
                last_seen = Stats.objects.first().api_last_seen
            except AttributeError:
                last_seen = None

            unacked = backend.job_requests.unacked().count()

            if show_warning(unacked, last_seen):
                yield backend.display_name

    backends = Backend.objects.all()
    return {"backend_warnings": list(iter_warnings(backends))}


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

    if request.user.is_superuser:
        options.append(
            {
                "name": "Backends",
                "is_active": _active(reverse("backend-list")),
                "url": reverse("backend-list"),
            }
        )

    return {"nav": options}
