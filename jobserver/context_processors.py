import functools

import structlog
from django.conf import settings
from django.db.models import Max
from django.urls import reverse
from furl import furl
from zen_queries import queries_dangerously_enabled

from .authorization import CoreDeveloper, has_role
from .backends import show_warning
from .models import Backend
from .nav import NavItem, iter_nav


logger = structlog.get_logger(__name__)


def _is_active(request, prefix):
    return request.path.startswith(prefix)


@queries_dangerously_enabled()
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


@queries_dangerously_enabled()
def can_view_staff_area(request):
    can_view_staff_area = has_role(request.user, CoreDeveloper)

    return {"user_can_view_staff_area": can_view_staff_area}


def disable_creating_jobs(request):
    return {"disable_creating_jobs": settings.DISABLE_CREATING_JOBS}


@queries_dangerously_enabled()
def staff_nav(request):
    if not has_role(request.user, CoreDeveloper):
        return {"staff_nav": []}

    is_active = functools.partial(_is_active, request)

    items = [
        NavItem(name="Analysis Requests", url_name="staff:analysis-request-list"),
        NavItem(name="Applications", url_name="staff:application-list"),
        NavItem(name="Backends", url_name="staff:backend-list"),
        NavItem(name="Dashboards", url_name="staff:dashboard:index"),
        NavItem(name="Orgs", url_name="staff:org-list"),
        NavItem(name="Redirects", url_name="staff:redirect-list"),
        NavItem(name="Projects", url_name="staff:project-list"),
        NavItem(name="Reports", url_name="staff:report-list"),
        NavItem(name="Repos", url_name="staff:repo-list"),
        NavItem(name="Users", url_name="staff:user-list"),
        NavItem(name="Workspaces", url_name="staff:workspace-list"),
    ]

    return {"staff_nav": list(iter_nav(items, request, is_active))}


def nav(request):
    is_active = functools.partial(_is_active, request)

    items = [
        NavItem(name="Event Log", url_name="job-list"),
        NavItem(name="Status", url_name="status"),
    ]

    return {"nav": list(iter_nav(items, request, is_active))}


def login_url(request):
    """Build the full login URL from any existing path parts"""
    f = furl(reverse("login"))

    # get the existing get args
    f.args.update(request.GET)

    # add the current path as the next parameter
    f.args.update({"next": request.path})

    return {"login_url": f.url}
