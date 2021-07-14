from django.core.exceptions import BadRequest


def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"


def raise_if_not_int(value):
    try:
        int(value)
    except ValueError:
        raise BadRequest


def set_from_qs(qs, field="pk"):
    return set(qs.values_list(field, flat=True))
