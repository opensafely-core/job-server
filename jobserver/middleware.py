from django.http import Http404

from .authorization import PermissionDenied


class PermissionDeniedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            # If this raised a 403 we could provide more context to the user.
            raise Http404
