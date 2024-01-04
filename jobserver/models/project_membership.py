import structlog
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..authorization.fields import RolesArrayField


logger = structlog.get_logger(__name__)


class ProjectMembership(models.Model):
    """
    Membership of a Project for a User

    Membership grants a User abilities in the context of the Project via the
    assigned Roles.
    """

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        related_name="created_project_memberships",
        null=True,
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    roles = RolesArrayField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["project", "user"]

    def __str__(self):
        return f"{self.user.username} | {self.project.title}"

    def get_staff_edit_url(self):
        return reverse(
            "staff:project-membership-edit",
            kwargs={
                "slug": self.project.slug,
                "pk": self.pk,
            },
        )

    def get_staff_remove_url(self):
        return reverse(
            "staff:project-membership-remove",
            kwargs={
                "slug": self.project.slug,
                "pk": self.pk,
            },
        )
