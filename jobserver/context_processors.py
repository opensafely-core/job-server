import functools

import structlog
from django.conf import settings
from django.urls import reverse

from .authorization import has_permission
from .backends import show_warning
from .models import Backend


logger = structlog.get_logger(__name__)


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def backend_warnings(request):
    def iter_warnings(backends):
        if settings.DEBUG:
            return

        for backend in backends:
            try:
                last_seen = (
                    backend.stats.order_by("-api_last_seen").first().api_last_seen
                )
            except AttributeError:
                logger.info(f"No stats found for backend '{backend.slug}'")
                continue

            if show_warning(last_seen):
                yield backend.name

    backends = Backend.objects.filter(is_active=True)
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

    if has_permission(request.user, "backend_manage"):
        options.append(
            {
                "name": "Backends",
                "is_active": _active(reverse("backend-list")),
                "url": reverse("backend-list"),
            }
        )

    if has_permission(request.user, "manage_users"):
        options.append(
            {
                "name": "Users",
                "is_active": _active(reverse("user-list")),
                "url": reverse("user-list"),
            }
        )

    return {"nav": options}


def scripts_attrs(request):
    """Generate script attributes for use with the Vite plugin"""
    return {
        "scripts_attrs": {"nomodule": ""},
    }
