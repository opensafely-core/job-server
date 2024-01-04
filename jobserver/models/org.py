import structlog
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


logger = structlog.get_logger(__name__)


def default_github_orgs():
    return list(["opensafely"])


class Org(models.Model):
    """An Organisation using the platform"""

    created_by = models.ForeignKey(
        "User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_orgs",
    )

    name = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(default="", blank=True)
    logo = models.TextField(default="", blank=True)
    logo_file = models.FileField(upload_to="org_logos/", null=True)

    # track which GitHub Organisations this Org has access to
    github_orgs = ArrayField(models.TextField(), default=default_github_orgs)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Organisation"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("org-detail", kwargs={"slug": self.slug})

    def get_edit_url(self):
        return reverse("staff:org-edit", kwargs={"slug": self.slug})

    def get_logs_url(self):
        return reverse("org-event-log", kwargs={"slug": self.slug})

    def get_staff_url(self):
        return reverse("staff:org-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)
