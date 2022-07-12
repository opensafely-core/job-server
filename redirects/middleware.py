from django.db.models.functions import Length
from django.shortcuts import redirect

from .models import Redirect


class RedirectsMiddleware:
    """
    Apply saved redirections to all requests

    We had three options for redirections, checked in this order:
     * exact match -> redirect
     * prefix match -> redirect
     * no match
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exemptions = (
            "/api",
            "/staff",
        )
        if request.path.startswith(exemptions):
            return self.get_response(request)

        # look for a direct or prefix match on the current URL
        redirection = (
            Redirect.objects.extra(
                where=["%s LIKE concat(old_url, '%%')"],
                params=[request.path],
            )
            .annotate(url_length=Length("old_url"))
            .order_by("-url_length")
            .first()
        )

        if redirection:
            return redirect(
                redirection.obj.get_absolute_url(),
                permanent=True,
            )

        # there's no direct or indirect match so let the request continue
        return self.get_response(request)
