import functools

import structlog
from django.conf import settings
from django.db.models import Max
from django.urls import reverse

from .authorization import CoreDeveloper, has_role
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
            if backend.api_last_seen is None:
                logger.info(f"No stats found for backend '{backend.slug}'")
                continue

            if show_warning(backend.api_last_seen, backend.alert_timeout):
                yield backend.name

    backends = Backend.objects.filter(is_active=True).annotate(
        api_last_seen=Max("stats__api_last_seen")
    )
    return {"backend_warnings": list(iter_warnings(backends))}


def can_view_staff_area(request):
    can_view_staff_area = has_role(request.user, CoreDeveloper)

    return {"user_can_view_staff_area": can_view_staff_area}


def disable_creating_jobs(request):
    return {"disable_creating_jobs": settings.DISABLE_CREATING_JOBS}


def staff_nav(request):
    if not has_role(request.user, CoreDeveloper):
        return {"staff_nav": []}

    _active = functools.partial(_is_active, request)

    options = [
        {
            "name": "Analysis Requests",
            "is_active": _active(reverse("staff:analysis-request-list")),
            "url": reverse("staff:analysis-request-list"),
        },
        {
            "name": "Applications",
            "is_active": _active(reverse("staff:application-list")),
            "url": reverse("staff:application-list"),
        },
        {
            "name": "Backends",
            "is_active": _active(reverse("staff:backend-list")),
            "url": reverse("staff:backend-list"),
        },
        {
            "name": "Dashboards",
            "is_active": _active(reverse("staff:dashboard:index")),
            "url": reverse("staff:dashboard:index"),
        },
        {
            "name": "Orgs",
            "is_active": _active(reverse("staff:org-list")),
            "url": reverse("staff:org-list"),
        },
        {
            "name": "Redirects",
            "is_active": _active(reverse("staff:redirect-list")),
            "url": reverse("staff:redirect-list"),
        },
        {
            "name": "Projects",
            "is_active": _active(reverse("staff:project-list")),
            "url": reverse("staff:project-list"),
        },
        {
            "name": "Reports",
            "is_active": _active(reverse("staff:report-list")),
            "url": reverse("staff:report-list"),
        },
        {
            "name": "Repos",
            "is_active": _active(reverse("staff:repo-list")),
            "url": reverse("staff:repo-list"),
        },
        {
            "name": "Users",
            "is_active": _active(reverse("staff:user-list")),
            "url": reverse("staff:user-list"),
        },
        {
            "name": "Workspaces",
            "is_active": _active(reverse("staff:workspace-list")),
            "url": reverse("staff:workspace-list"),
        },
    ]

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
