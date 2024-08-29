import structlog
from django.db import models
from django.utils import timezone


logger = structlog.get_logger(__name__)


class OrgMembership(models.Model):
    """Membership of an Organistion for a User"""

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_org_memberships",
        null=True,
    )
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["org", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.org.name}"
