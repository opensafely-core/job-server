from django.db.models import Count
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import View

from ..backends import show_warning
from ..models import Backend, Job


class DBAvailability(View):
    def get(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, slug=self.kwargs["backend"])

        if backend.slug != "tpp":
            return HttpResponse(
                f"DB maintenance mode not implemented in {backend.name}"
            )

        mode = backend.jobrunner_state.get("mode", {})

        # conver the timestamp into
        suffix = ""
        if timestamp := mode.get("ts", ""):
            suffix = f" (since {timestamp}) "

        if mode.get("v", "") == "db-maintenance":
            return HttpResponse(f"DB maintenance mode on{suffix}", status=503)

        return HttpResponse(f"DB maintenance mode off{suffix}")


class PerBackendStatus(View):
    def get(self, request, *args, **kwargs):
        backend = get_object_or_404(Backend, slug=self.kwargs["backend"])

        try:
            last_seen = backend.stats.order_by("-api_last_seen").first().api_last_seen
        except AttributeError:
            # don't show Backends which have never checked in as an error
            last_seen = timezone.now()

        # how long ago did we last see this backend?
        time_since_last_seen = timezone.now() - last_seen

        # do we consider the backend missing?
        is_missing = time_since_last_seen > backend.alert_timeout

        # set a status code of 503 if the backend was last seen longer than the
        # configured value ago
        status_code = 503 if is_missing else 200

        return HttpResponse(last_seen.isoformat(), status=status_code)


class Status(View):
    def get(self, request, *args, **kwargs):
        def get_stats(backend):
            acked = (
                backend.job_requests.annotate(num_jobs=Count("jobs"))
                .filter(num_jobs__gt=0)
                .count()
            )
            unacked = (
                backend.job_requests.annotate(num_jobs=Count("jobs"))
                .filter(num_jobs=0)
                .count()
            )
            counts_by_status = (
                Job.objects.filter(
                    job_request__backend=backend,
                    status__in=["running", "pending"],
                )
                .values("status")
                .annotate(count=Count("status"))
            )
            pending = running = 0
            for result in counts_by_status:
                if result["status"] == "pending":
                    pending = result["count"]
                if result["status"] == "running":
                    running = result["count"]

            try:
                last_seen = (
                    backend.stats.order_by("-api_last_seen").first().api_last_seen
                )
            except AttributeError:
                last_seen = None

            return {
                "name": backend.name,
                "alert_timeout": backend.alert_timeout,
                "last_seen": last_seen,
                "queue": {
                    "acked": acked,
                    "unacked": unacked,
                    "running": running,
                    "pending": pending,
                },
                "show_warning": show_warning(last_seen, backend.alert_timeout),
            }

        backends = Backend.objects.filter(is_active=True).order_by(Lower("name"))
        context = {"backends": [get_stats(b) for b in backends]}
        return TemplateResponse(request, "status.html", context)
