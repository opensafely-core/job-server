from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from jobserver.models.backends import Backend


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


class ClientAddressIdentification:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META["REMOTE_ADDR"]
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = self.get_forwarded_ip(forwarded, ip, settings.TRUSTED_PROXIES)

        slug = settings.BACKEND_IP_MAP.get(ip)
        if slug:
            request.backend = Backend.objects.get(slug=slug)
        else:
            request.backend = None
        return self.get_response(request)

    def get_forwarded_ip(self, forwarded, remote_addr, trusted_ips):
        """Walk ips from right to left, returning the first non-trusted ip left of a trusted ip.

        This means spoofed IPs should be ignored, as they not be after a trusted proxy.
        """
        ips = [ip.strip() for ip in forwarded.split(",")] + [remote_addr]
        for ip in reversed(ips):
            trusted = ip in trusted_ips
            if not trusted:
                return ip

        return ip
