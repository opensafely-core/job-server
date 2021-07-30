import binascii
import os

from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..backends import get_configured_backends


def generate_token():
    """Generate a random token string."""
    return binascii.hexlify(os.urandom(20)).decode()


class BackendManager(models.Manager):
    def get_queryset(self):
        """
        Override default QuerySet to limit backends to those configured

        We want to limit the available backends from the database to those
        configured in the environment without changing the backed in model
        validation. Each Backend is created via a migration.  This function
        limits which backends can be looked up via the ORM to the set listed in
        the env.
        """
        # lookup configured backends on demand to make testing easier
        configured_backends = get_configured_backends()

        qs = super().get_queryset()

        if not configured_backends:
            # if no backends are configured, make all available
            return qs

        return qs.filter(name__in=configured_backends)


class Backend(models.Model):
    """A job-runner instance"""

    name = models.TextField(unique=True)
    display_name = models.TextField()

    parent_directory = models.TextField(default="")
    is_active = models.BooleanField(default=False)

    auth_token = models.TextField(default=generate_token)

    # track where release-hatch is serving files from
    level_4_url = models.TextField(default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BackendManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("backend-detail", kwargs={"pk": self.pk})

    def get_edit_url(self):
        return reverse("backend-edit", kwargs={"pk": self.pk})

    def get_rotate_url(self):
        return reverse("backend-rotate-token", kwargs={"pk": self.pk})

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
        return f"{self.user.username} | {self.backend.display_name}"
