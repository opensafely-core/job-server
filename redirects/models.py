from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


def default_expires_at():
    return timezone.now() + timedelta(days=365)


# FIXME: remove next time we squash migrations
def validate_not_empty(value):  # pragma: no cover
    if not bool(value):
        raise ValidationError("empty is not a valid value", params={"value": value})


class Redirect(models.Model):
    analysis_request = models.ForeignKey(
        "interactive.AnalysisRequest",
        on_delete=models.CASCADE,
        related_name="redirects",
        null=True,
    )
    org = models.ForeignKey(
        "jobserver.Org",
        on_delete=models.CASCADE,
        related_name="redirects",
        null=True,
    )
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

    old_url = models.TextField(db_index=True)
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
                check=~Q(old_url=""),
                name="old_url_is_not_empty",
            ),
            models.CheckConstraint(
                check=Q(old_url__endswith="/") & Q(old_url__startswith="/"),
                name="old_url_endswith_and_startswith_slash",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        deleted_at__isnull=True,
                        deleted_by__isnull=True,
                    )
                    | (
                        Q(
                            deleted_at__isnull=False,
                            deleted_by__isnull=False,
                        )
                    )
                ),
                name="%(app_label)s_%(class)s_both_deleted_at_and_deleted_by_set",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        analysis_request__isnull=False,
                        org__isnull=True,
                        project__isnull=True,
                        workspace__isnull=True,
                    )
                    | Q(
                        analysis_request__isnull=True,
                        org__isnull=False,
                        project__isnull=True,
                        workspace__isnull=True,
                    )
                    | Q(
                        analysis_request__isnull=True,
                        org__isnull=True,
                        project__isnull=False,
                        workspace__isnull=True,
                    )
                    | Q(
                        analysis_request__isnull=True,
                        org__isnull=True,
                        project__isnull=True,
                        workspace__isnull=False,
                    )
                ),
                name="%(app_label)s_%(class)s_only_one_target_model_set",
            ),
        ]

    def __str__(self):
        return self.old_url

    def get_staff_url(self):
        return reverse("staff:redirect-detail", kwargs={"pk": self.pk})

    def get_staff_delete_url(self):
        return reverse("staff:redirect-delete", kwargs={"pk": self.pk})

    @property
    def obj(self):
        """Work out which object we're pointing to"""
        field_names = [getattr(self, f.name, None) for f in self.targets()]
        return next((f for f in field_names if f), None)

    @classmethod
    def targets(cls):
        """
        Get target ForeignKey fields

        This is a classmethod so users without a Redirect instance can still
        make use of it.
        """
        return [
            f
            for f in cls._meta.fields
            if getattr(f, "related_query_name", lambda: "")() == "redirects"
        ]

    @property
    def type(self):  # noqa: A003
        return self.obj.__class__.__name__

    def save(self, *args, **kwargs):
        # TODO: check old_url doesn't match any path for the given redirect target
        # this avoids us creating a redirect loop by adding a redirect here
        return super().save(*args, **kwargs)
