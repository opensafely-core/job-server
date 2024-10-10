import functools

import structlog
from django.conf import settings
from django.urls import reverse
from furl import furl

from .authorization import StaffAreaAdministrator, has_role
from .nav import NavItem, iter_nav


logger = structlog.get_logger(__name__)


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def can_view_staff_area(request):
    can_view_staff_area = has_role(request.user, StaffAreaAdministrator)

    return {"user_can_view_staff_area": can_view_staff_area}


def disable_creating_jobs(request):
    return {"disable_creating_jobs": settings.DISABLE_CREATING_JOBS}


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
