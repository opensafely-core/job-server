import structlog
from django.db import models
from django.utils import timezone


logger = structlog.get_logger(__name__)


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
