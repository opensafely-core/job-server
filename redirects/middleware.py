from django.db.models import CharField, F, Value
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
            Redirect.objects.annotate(
                url_length=Length("old_url"),
                request_url=Value(request.path, output_field=CharField()),
            )
            .filter(request_url__startswith=F("old_url"))
            .order_by("-url_length")
            .first()
        )

        if not redirection:
            # there's no direct or indirect match so let the request continue
            return self.get_response(request)

        if redirection.old_url == request.path:
            return redirect(
                redirection.obj.get_absolute_url(),
                permanent=True,
            )

        new_url = request.path.replace(
            redirection.old_url, redirection.obj.get_absolute_url()
        )
        return redirect(new_url, permanent=True)
