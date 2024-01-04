import binascii
import os
from datetime import timedelta

import structlog
from django.db import models
from django.urls import reverse
from django.utils import timezone


logger = structlog.get_logger(__name__)


def generate_token():
    """Generate a random token string."""
    return binascii.hexlify(os.urandom(20)).decode()


class Backend(models.Model):
    """A job-runner instance"""

    slug = models.SlugField(max_length=255, unique=True)
    name = models.TextField()

    parent_directory = models.TextField(default="", blank=True)
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

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

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
