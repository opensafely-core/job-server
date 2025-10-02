import binascii
import os
from datetime import timedelta

import structlog
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone


logger = structlog.get_logger(__name__)


def generate_token():
    """Generate a random token string."""
    return binascii.hexlify(os.urandom(20)).decode()


class BackendManager(models.Manager):
    def get_db_maintenance_mode_statuses(self, cache_duration=60):
        """
        Return a mapping of backend slugs to a boolean indicating
        whether each is in database maintenance mode.

        Only the "tpp" and "emis" backends are checked.

        Results are cached (default 60s) to align with the RAP API cron
        schedule defined in app.json, reducing database queries.
        """

        cache_key = f"{__name__}.backend_maintenance_statuses"
        statuses = cache.get(cache_key)

        if statuses is None:
            statuses = {}
            allowed_backends = ["tpp", "emis"]

            backend_statuses = (
                self.get_queryset()
                .filter(slug__in=allowed_backends)
                .values("slug", "is_in_maintenance_mode")
            )

            statuses = {
                backend["slug"]: backend["is_in_maintenance_mode"]
                for backend in backend_statuses
            }

            cache.set(cache_key, statuses, cache_duration)

        return statuses


class Backend(models.Model):
    """A job-runner instance"""

    slug = models.SlugField(max_length=255, unique=True)
    name = models.TextField()

    is_active = models.BooleanField(
        default=False,
        help_text="Is this backend currently active on the platform?  Connectivity warnings are only shown for active backends.",
    )

    auth_token = models.TextField(default=generate_token)

    # how long until we consider a backend to be missing
    alert_timeout = models.DurationField(default=timedelta(minutes=5))

    rap_api_state = models.JSONField(null=True)

    last_seen_at = models.DateTimeField(null=True)

    # date and time maintenance mode was last updated (i.e. when it was last turned on or off)
    last_seen_maintenance_mode = models.DateTimeField(null=True)

    is_in_maintenance_mode = models.BooleanField(
        default=False,
        help_text="Is this backend currently in database maintenance mode?",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BackendManager()

    def __str__(self):
        return self.slug

    def get_edit_url(self):
        return reverse("staff:backend-edit", kwargs={"pk": self.pk})

    def get_rotate_url(self):
        return reverse("staff:backend-rotate-token", kwargs={"pk": self.pk})

    def get_staff_url(self):
        return reverse("staff:backend-detail", kwargs={"pk": self.pk})

    def rotate_token(self):
        self.auth_token = generate_token()
        self.save()
