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
