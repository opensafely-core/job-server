from django.conf import settings

from jobserver.models.backends import Backend


class XSSFilteringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        return response


class ClientAddressIdentification:
    """Detect if client IP address is commng from a Level 4 IP address.

    In the simple local dev case, there is no proxy, so we just use
    REMOTE_ADDR. When we are behind nginx, we use the standard X-Forwarded-For
    header.

    However, this header is additive per proxy, and can be easily spoofed. So
    we use a list of trusted proxy IP addresses to figure out which is the
    trusted source address. Note: we will probably strip it from nginx too,
    which also solves the problem, but we don't want to rely on that alone, as
    it could change.

    Note:  we are deliberately constraining this implementation to only support
    X-Forwarded-For in the standard format, because that's what nginx does.
    We're ignoring X-Real-IP and others, as well as unusual headers formats, as
    we only need this one specific case to work.

    Note: we attempted using the structlog dependency django-ipware for this,
    but its trusted proxy list support seems be incorrectly implemented.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # this can be trusted, it's from the WSGI environ.
        ip = request.META["REMOTE_ADDR"]
        # this cannot be trusted, as it may have been spoofed
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

        This means spoofed X-Forwarded-For IPs will be ignored, as they will not be
        directly after a trusted proxy.
        """
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()] + [remote_addr]
        for ip in reversed(ips):
            trusted = any(ip.startswith(tip) for tip in trusted_ips)
            if not trusted:
                return ip

        return ip
