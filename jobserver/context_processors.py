import functools

import structlog
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from furl import furl

from .authorization import StaffAreaAdministrator, has_role
from .models import Backend, SiteAlert
from .nav import NavItem, iter_nav


logger = structlog.get_logger(__name__)

BANNER_DISPLAY_URL_NAMES = {
    "job-detail",
    "job-request-create",
    "job-request-detail",
    "status",
    "workspace-logs",
}


def in_production(request):
    """Is the site operating in production mode?

    As determined by settings.py / environment variables."""
    return {"in_production": not settings.DEBUG}


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def can_view_staff_area(request):
    user = getattr(request, "user", None) or AnonymousUser()
    return {"user_can_view_staff_area": has_role(user, StaffAreaAdministrator)}


def disable_creating_jobs(request):
    return {
        "disable_creating_jobs": settings.DISABLE_CREATING_JOBS,
    }


def site_alerts(request):
    """Add all SiteAlert instances to the context for authenticated users.

    Unauthenticated users probably don't need details of alerts that affect
    users of the site."""
    user = getattr(request, "user", None) or AnonymousUser()
    return {
        "site_alerts": SiteAlert.objects.all() if user.is_authenticated else None,
    }


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


def db_maintenance_mode(request):
    """Add database maintenance banner flags to context for specific
    views."""

    if (
        request.resolver_match
        and request.resolver_match.url_name in BANNER_DISPLAY_URL_NAMES
    ):
        maintenance_statuses = Backend.objects.get_db_maintenance_mode_statuses()
        return {
            f"{backend}_maintenance_banner": status
            for backend, status in maintenance_statuses.items()
        }
    return {}
