from django.core.exceptions import BadRequest


def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"


def raise_if_not_int(value):
    try:
        int(value)
    except ValueError:
        raise BadRequest
