from django.db import models
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField


class Report(models.Model):
    release_file = models.ForeignKey(
        "ReleaseFile",
        on_delete=models.PROTECT,
        related_name="reports",
    )

    title = models.TextField()
    slug = AutoSlugField(max_length=100, populate_from=["title"], unique=True)
    description = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_created",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_updated",
    )

    published_at = models.DateTimeField(null=True)
    published_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="reports_published",
        null=True,
    )

    def __str__(self):
        return self.title
