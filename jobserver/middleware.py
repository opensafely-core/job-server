from django.shortcuts import redirect
from django.urls import reverse


class RequireNameMiddleware:
    """
    Redirect users without `fullname` set to the settings page

    We get a User's username from GitHub when they register with the site.  If
    their GitHub profile has a name set we also get that, however we have many
    (~50% at time of writing) users who have not set that.  We want to require
    all users have their name set.  This middleware redirects any user with an
    empty `fullname` value to their settings page.

    We exempt various URL prefixes which don't make sense to do this on, eg if
    we're not expecting traditional users there or it doesn't make sense for
    the UX (in the case of applications).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Note: ordered by expected popularity then name
        exemptions = (
            "/api",
            "/staff",
            "/robots.txt",
            "/__debug__",
            "/__reload__",
            "/applications",
            "/apply",
            "/complete",
            "/disconnect",
            "/favicon.ico",
            "/login",
            "/logout",
            "/settings",
            "/status",
        )

        # unauthenticated users can't set their name
        if not request.user.is_authenticated:
            return self.get_response(request)

        # we don't want to redirect requests away from various URL paths
        if request.path.startswith(exemptions):
            return self.get_response(request)

        # we only care about users without a fullname set
        if request.user.fullname != "":
            return self.get_response(request)

        return redirect(reverse("settings") + f"?next={request.path}")


class XSSFilteringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        return response
