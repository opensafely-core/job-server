from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from first import first


def default_expires_at():
    return timezone.now() + timedelta(days=365)


def validate_not_empty(value):
    if not bool(value):
        raise ValidationError("empty is not a valid value", params={"value": value})


class Redirect(models.Model):
    project = models.ForeignKey(
        "jobserver.Project",
        on_delete=models.CASCADE,
        related_name="redirects",
        null=True,
    )
    workspace = models.ForeignKey(
        "jobserver.Workspace",
        on_delete=models.CASCADE,
        related_name="redirects",
        null=True,
    )

    old_url = models.TextField(validators=[validate_not_empty], db_index=True)
    expires_at = models.DateTimeField(default=default_expires_at)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "jobserver.User",
        on_delete=models.PROTECT,
        related_name="redirects_created",
    )

    updated_at = models.DateTimeField(auto_now=True)

    deleted_at = models.DateTimeField(null=True)
    deleted_by = models.ForeignKey(
        "jobserver.User",
        null=True,
        on_delete=models.PROTECT,
        related_name="redirect_deleted",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(deleted_at=None) & Q(deleted_by=None))
                    | (~Q(deleted_at=None) & ~Q(deleted_by=None))
                ),
                name="%(app_label)s_%(class)s_both_deleted_at_and_deleted_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(project__isnull=True, workspace__isnull=False)
                    | Q(project__isnull=False, workspace__isnull=True)
                ),
                name="%(app_label)s_%(class)s_only_one_target_model_set",
            ),
        ]

    @property
    def obj(self):
        """Work out which object we're pointing to"""
        return first([self.project, self.workspace])

    def save(self, *args, **kwargs):
        # TODO: check old_url doesn't match any path for the given redirect target
        # this avoids us creating a redirect loop by adding a redirect here
        return super().save(*args, **kwargs)
