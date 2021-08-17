import functools

import structlog
from django.conf import settings
from django.urls import reverse

from .authorization import CoreDeveloper, has_permission, has_role
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


def can_view_staff_area(request):
    can_view_staff_area = has_role(request.user, CoreDeveloper)

    return {"user_can_view_staff_area": can_view_staff_area}


def staff_nav(request):
    if not request.user.is_authenticated:
        return {"staff_nav": []}

    _active = functools.partial(_is_active, request)

    options = []

    if has_permission(request.user, "backend_manage"):
        options.append(
            {
                "name": "Backends",
                "is_active": _active(reverse("staff:backend-list")),
                "url": reverse("staff:backend-list"),
            }
        )

    if has_permission(request.user, "user_manage"):
        options.append(
            {
                "name": "Users",
                "is_active": _active(reverse("staff:user-list")),
                "url": reverse("staff:user-list"),
            }
        )

    return {"staff_nav": options}


def nav(request):
    _active = functools.partial(_is_active, request)

    return {
        "nav": [
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
        ],
    }


def scripts_attrs(request):
    """Generate script attributes for use with the Vite plugin"""
    return {
        "scripts_attrs": {"nomodule": ""},
    }
