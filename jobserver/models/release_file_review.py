import structlog
from django.db import models
from django.db.models import Q


logger = structlog.get_logger(__name__)


class ReleaseFileReview(models.Model):
    class Statuses(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    release_file = models.ForeignKey(
        "ReleaseFile",
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    status = models.TextField(choices=Statuses.choices)
    comments = models.JSONField()

    # no default here because this needs to match for all reviews created at
    # the same time.
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="release_file_reviews",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(
                        created_at__isnull=True,
                        created_by__isnull=True,
                    )
                    | (
                        Q(
                            created_at__isnull=False,
                            created_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_created_at_and_created_by_set",
            ),
        ]
