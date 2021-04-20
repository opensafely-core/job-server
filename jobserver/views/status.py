from django.template.response import TemplateResponse
from django.views.generic import View

from ..backends import show_warning
from ..models import Backend


class Status(View):
    def get(self, request, *args, **kwargs):
        def format_last_seen(last_seen):
            if last_seen is None:
                return "never"

            return last_seen.strftime("%Y-%m-%d %H:%M:%S")

        def get_stats(backend):
            acked = backend.job_requests.acked().count()
            unacked = backend.job_requests.unacked().count()

            try:
                last_seen = (
                    backend.stats.order_by("-api_last_seen").first().api_last_seen
                )
            except AttributeError:
                last_seen = None

            return {
                "name": backend.display_name,
                "last_seen": format_last_seen(last_seen),
                "queue": {
                    "acked": acked,
                    "unacked": unacked,
                },
                "show_warning": show_warning(last_seen),
            }

        backends = Backend.objects.all()
        context = {"backends": [get_stats(b) for b in backends]}
        return TemplateResponse(request, "status.html", context)
