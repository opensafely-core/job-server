from django.apps import apps
from django.db import models


_SKIP_APP_LABELS = {"auth", "contenttypes", "sessions", "social_django"}


def get_models():
    """
    Return a list of all installed, project-specific models.
    """
    return [
        model
        for model in apps.get_models()
        if model._meta.app_label not in _SKIP_APP_LABELS
    ]


class ImmutableError(TypeError):
    pass


def _raise_error(model):
    model_name = model._meta.label.split(".")[1]
    raise ImmutableError(f"Direct access to {model_name} is disabled")


class ImmutableModelMixin:
    def delete(self, *args, override=False, **kwargs):
        if not override:
            _raise_error(self)
        super().delete(*args, **kwargs)

    def save(self, *args, override=False, **kwargs):
        if not override:
            _raise_error(self)
        super().save(*args, **kwargs)


class ImmutableQuerySet(models.QuerySet):
    # We don't override get_or_create, because we don't want to disable the get part.
    # The create part delegates to create.

    def bulk_create(self, *args, **kwargs):
        _raise_error(self.model)

    def bulk_update(self, *args, **kwargs):
        _raise_error(self.model)

    def create(self, *args, **kwargs):
        _raise_error(self.model)

    def delete(self, *args, **kwargs):
        _raise_error(self.model)

    def update(self, *args, **kwargs):
        _raise_error(self.model)

    def update_or_create(self, *args, **kwargs):
        _raise_error(self.model)


class ImmutableManager(models.Manager.from_queryset(ImmutableQuerySet)):
    pass
