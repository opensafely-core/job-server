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
        Return a dictionary mapping backend slugs to their database (db)maintenance mode status value (True/False). Values are cached to reduce the number of database queries. Querying is limited a list of allowed_backends which currently includes "tpp" and "emis".
        """
        cache_key = "backend_maintenance_statuses"
        statuses = cache.get(cache_key)

        if statuses is None:
            statuses = {}
            allowed_backends = ["tpp", "emis"]

            backend_jr_state_values = (
                self.get_queryset()
                .filter(slug__in=allowed_backends)
                .values("slug", "jobrunner_state")
            )

            for row in backend_jr_state_values:
                jobrunner_state = row["jobrunner_state"] or {}
                in_maintenance = (
                    jobrunner_state.get("mode", {}).get("v") == "db-maintenance"
                )
                statuses[row["slug"]] = in_maintenance

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

    # track where release-hatch is serving files from
    level_4_url = models.TextField(default="", blank=True)

    # how long until we consider a backend to be missing
    alert_timeout = models.DurationField(default=timedelta(minutes=5))

    jobrunner_state = models.JSONField(null=True)

    rap_api_state = models.JSONField(null=True)

    last_seen_at = models.DateTimeField(null=True)

    last_seen_maintenance_mode = models.DateTimeField(null=True)

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
