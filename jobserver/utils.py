from urllib.parse import urlparse

from django.core.exceptions import BadRequest


def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"


def is_safe_path(path):
    """If `path` is safe, then returns `True`. Otherwise returns `False`.

    A safe path has neither a scheme (e.g. "https") nor a location (e.g.
    "www.opensafely.org").
    """
    parse_result = urlparse(path)
    return not (parse_result.scheme or parse_result.netloc)


def raise_if_not_int(value):
    try:
        int(value)
    except ValueError:
        raise BadRequest


def set_from_qs(qs, field="pk"):
    return set(qs.values_list(field, flat=True))
