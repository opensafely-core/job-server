"""Site-wide alerts to display to authenticated users."""

from django.db import models
from django.urls import reverse

from .user import User


class SiteAlert(models.Model):
    """A site-wide alert to display to authenticated users."""

    class Level(models.TextChoices):
        """Choices for the level attribute (html_name, human_readable)."""

        DANGER = "danger", "Danger"
        INFO = "info", "Info"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"

    title = models.TextField(
        blank=True,
        help_text="Summary of the reason for the alert, to display in the title of the alert (optional)",
    )
    """Optional heading summarizing the reason for the alert"""
    message = models.TextField(
        help_text="The message to display in the alert (required)"
    )
    """The body of the alert. Can include embedded HTML."""
    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        default=Level.WARNING,
        help_text="How significant the alert is, for UI styling.",
    )
    """How significant the alert is, which affects UI styling."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        related_name="site_alerts_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        User,
        related_name="site_alerts_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.get_level_display()}: {self.title or self.message}"

    def __repr__(self):
        return f"<SiteAlert title: '{self.title}' message: '{self.message}' level: {self.level}>"

    class Meta:
        ordering = ["-created_at"]

    @property
    def edit_url(self):
        """URL to edit the site alert."""
        return reverse("staff:site-alerts:edit", kwargs={"pk": self.pk})

    @property
    def delete_url(self):
        """URL to delete the site alert."""
        return reverse("staff:site-alerts:delete", kwargs={"pk": self.pk})
