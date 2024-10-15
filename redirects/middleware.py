from django.db.models import CharField, F, Value
from django.db.models.functions import Length
from django.shortcuts import redirect

from .models import Redirect


class RedirectsMiddleware:
    """Apply DB redirects to rewrite request URLs, with longer matches
    preferred. Exact matches take top priority."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip processing requests for non-user-facing URLs.
        exemptions = (
            "/api",
            "/staff",
        )
        if request.path.startswith(exemptions):
            return self.get_response(request)

        # Find the longest old_url that matches the start of request.path
        # (longer URLs are more specific). Exact matches take top priority.
        redirection = (
            Redirect.objects.annotate(
                url_length=Length("old_url"),
                request_url=Value(request.path, output_field=CharField()),
            )
            .filter(request_url__startswith=F("old_url"))
            .order_by("-url_length")
            .first()
        )

        # No match, allow the request to proceed.
        if not redirection:
            return self.get_response(request)

        # Exact match, return the URL from the DB.
        if redirection.old_url == request.path:
            return redirect(
                redirection.obj.get_absolute_url(),
                permanent=True,
            )

        # Partial match, rewrite the request URL prefix.
        new_url = request.path.replace(
            redirection.old_url, redirection.obj.get_absolute_url()
        )
        return redirect(new_url, permanent=True)
