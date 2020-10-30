from django.urls import reverse
from django.utils import timezone

from .models import Stats


API_PREFIX = reverse("api-root")


def stats_middleware(get_response):
    def middleware(request):
        response = get_response(request)

        if not request.path.startswith(API_PREFIX):
            return response

        # only update the stats for API access
        Stats.objects.update_or_create(pk=1, defaults={"api_last_seen": timezone.now()})

        return response

    return middleware
