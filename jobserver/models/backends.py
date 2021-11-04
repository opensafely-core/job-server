import binascii
import os

from django.db import models
from django.urls import reverse
from django.utils import timezone


def generate_token():
    """Generate a random token string."""
    return binascii.hexlify(os.urandom(20)).decode()


class Backend(models.Model):
    """A job-runner instance"""

    slug = models.SlugField(max_length=255, unique=True)
    name = models.TextField()

    parent_directory = models.TextField(default="", blank=True)
    is_active = models.BooleanField(default=False)

    auth_token = models.TextField(default=generate_token)

    # track where release-hatch is serving files from
    level_4_url = models.TextField(default="", blank=True)

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


class BackendMembership(models.Model):
    """Models the ability for a User to run jobs against a Backend."""

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_backend_memberships",
        null=True,
    )
    backend = models.ForeignKey(
        "Backend",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="backend_memberships",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["backend", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.backend.name}"
